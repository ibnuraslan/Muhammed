"""Animation, camera, cutaways for DwarfGiant.  blender -b scene.blend --python 03_anim.py -- <pipeline_dir> <out.blend>"""
import bpy, bmesh, sys, os, math, random
from mathutils import Vector, Matrix, Euler
a = sys.argv[sys.argv.index("--") + 1:]
PIPE, OUT = a[0], a[1]
exec(open(os.path.join(PIPE, "anim_lib.py")).read())
random.seed(26)
sc = bpy.context.scene
V = lambda *v: Vector(v)
OB = bpy.data.objects

def fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    out = []
    for layer in ad.action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags: out += list(cb.fcurves)
    return out

def const_keys(idb, frames=None, path=None):
    for fc in fcurves(idb):
        if path and not fc.data_path.startswith(path): continue
        for kp in fc.keyframe_points:
            if frames is None or int(round(kp.co.x)) in frames: kp.interpolation = "CONSTANT"

def vis(o, ranges):
    """ranges: list of (f0, f1) where object renders; constant keys"""
    o.hide_render = True; o.keyframe_insert("hide_render", frame=1)
    for f0, f1 in ranges:
        o.hide_render = False; o.keyframe_insert("hide_render", frame=f0)
        o.hide_render = True; o.keyframe_insert("hide_render", frame=f1 + 1)
    const_keys(o, path="hide_render")
    o.hide_viewport = False

def hide_ranges(o, ranges):
    o.hide_render = False; o.keyframe_insert("hide_render", frame=1)
    for f0, f1 in ranges:
        o.hide_render = True; o.keyframe_insert("hide_render", frame=f0)
        o.hide_render = False; o.keyframe_insert("hide_render", frame=f1 + 1)
    const_keys(o, path="hide_render")

def meshes_of(rig): return [o for o in OB if o.parent == rig and o.type == "MESH"]
def yaw_to(p, q):
    d = (q - p).to_2d(); return math.degrees(math.atan2(d.x, -d.y))   # 0 = facing -Y

# ------------------------------------------------------------------ material tints (uniforms, scrubs, dark suits) + shirt print check
def tint_mat(obj, rgb, rough=None):
    for i, m in enumerate(obj.data.materials):
        if not m: continue
        m2 = m.copy(); obj.data.materials[i] = m2
        nt = m2.node_tree
        for n in list(nt.nodes):
            if n.type == "BSDF_PRINCIPLED":
                inp = n.inputs["Base Color"]
                if inp.links:
                    src = inp.links[0].from_socket
                    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs[0].default_value = 1.0
                    hsv = nt.nodes.new("ShaderNodeHueSaturation"); hsv.inputs["Saturation"].default_value = 0.0; hsv.inputs["Value"].default_value = 2.6
                    nt.links.new(src, hsv.inputs["Color"]); nt.links.new(hsv.outputs[0], mx.inputs[6])
                    mx.inputs[7].default_value = (*rgb, 1); nt.links.new(mx.outputs[2], inp)
                else:
                    inp.default_value = (*rgb, 1)
                if rough is not None and not n.inputs["Roughness"].links: n.inputs["Roughness"].default_value = rough
def uniform_mat(obj, wool):
    """black suit texture -> field-grey/olive wool via a luminance ramp (suit dark -> wool colour, shirt light -> khaki shirt)"""
    for i, m in enumerate(obj.data.materials):
        m2 = m.copy(); obj.data.materials[i] = m2; nt = m2.node_tree
        b = nt.nodes["Principled BSDF"]; src = nt.nodes["diffuseIntensity"].outputs[0]
        bw = nt.nodes.new("ShaderNodeRGBToBW"); rp = nt.nodes.new("ShaderNodeValToRGB"); cr = rp.color_ramp
        cr.elements[0].position = 0.0; cr.elements[0].color = (wool[0] * 0.35, wool[1] * 0.35, wool[2] * 0.35, 1)
        cr.elements[1].position = 0.12; cr.elements[1].color = (*wool, 1)
        e = cr.elements.new(0.35); e.color = (0.55, 0.52, 0.42, 1)
        e = cr.elements.new(0.8); e.color = (0.78, 0.75, 0.64, 1)
        nt.links.new(src, bw.inputs[0]); nt.links.new(bw.outputs[0], rp.inputs[0]); nt.links.new(rp.outputs[0], b.inputs["Base Color"])
        b.inputs["Roughness"].default_value = 0.85
uniform_mat(OB["Officer1.male_elegantsuit01"], (0.30, 0.31, 0.19))
uniform_mat(OB["Officer2.male_elegantsuit01"], (0.27, 0.29, 0.24))
for nm in ("Surgeon1", "Surgeon2"):
    tint_mat(OB[f"{nm}.male_worksuit01"], (0.62, 0.72, 0.66))
tint_mat(OB["Nurse.female_elegantsuit01"], (0.9, 0.9, 0.88))
# hero keeps the worksuit's own clear colours: white shirt + blue dungarees (reads as clothed at thumbnail size)
tint_mat(OB["Clerk.male_elegantsuit01"], (0.18, 0.17, 0.16))

# ------------------------------------------------------------------ rigs
for o in OB:                       # subdivision after the helper masks (else helper geometry balloons)
    if o.type == "MESH" and "Subdivision" in o.modifiers:
        n = len(o.modifiers) - 1
        with bpy.context.temp_override(object=o): bpy.ops.object.modifier_move_to_index(modifier="Subdivision", index=n)
RIGS = {n: OB["RIG_" + n] for n in ("Hero", "Young", "Officer1", "Officer2", "Clerk", "Recruit1", "Recruit2", "Surgeon1", "Surgeon2", "Nurse", "Normal")}
HU = {}
for n in ("Hero", "Officer1", "Officer2", "Young", "Normal", "Clerk", "Surgeon1", "Surgeon2", "Nurse"):
    HU[n] = Human(make_human_ctrl(RIGS[n]))
FK = {n: Rig(RIGS[n]) for n in RIGS if n not in HU}
for r in FK.values():
    for pb in r.PB: pb.rotation_mode = "QUATERNION"

def place(n, f, loc, yaw, scale=None, rx=0.0, const=False):
    o = RIGS[n]; o.location = loc; o.rotation_euler = (R_(rx), 0, R_(yaw))
    o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None:
        o.scale = (scale,) * 3; o.keyframe_insert("scale", frame=f)
    if const: const_keys(o, {f})

def arms_down_fk(r, f, out=12, bend=12, sway=0.0):
    r.key_rot("upperarm01.L", f, [("Y", 48 - out + sway), ("X", -6)]); r.key_rot("upperarm01.R", f, [("Y", -48 + out - sway), ("X", -6)])
    r.key_rot("lowerarm01.L", f, [("X", -bend)]); r.key_rot("lowerarm01.R", f, [("X", -bend)])

def body_fk(r, f, flex=0.0, twist=0.0, side=0.0, head=(0, 0), yaw_root=0.0):
    for n, w in Human.SPINE_W.items(): r.key_rot(n, f, [("X", flex * w), ("Y", side * w), ("Z", twist * w)])
    for n, w in Human.HEAD_W.items(): r.key_rot(n, f, [("X", head[0] * w), ("Z", head[1] * w)])

def jaw(r, f, open_deg): r.key_rot("jaw", f, [("X", open_deg)])

def talk(r, f0, f1, amp=9, rate=7):
    for f in range(f0, f1, rate):
        jaw(r, f, amp * (0.3 + 0.7 * random.random())); jaw(r, f + rate // 2, 1.0)

def brows(r, f, up=0.0, frown=0.0, squint=0.0):
    """face bones verified in close-up: oculi02 +X = brows down/knit (frown), oculi01 -X + orbicularis03 +X = brows up + lids wide,
    orbicularis04 +X = squint/close"""
    for sd in "LR":
        r.key_q("oculi02." + sd, f, Quaternion((1, 0, 0), R_(min(30, frown * 1.6))))
        r.key_q("oculi01." + sd, f, Quaternion((1, 0, 0), R_(-up * 1.8)))
        r.key_q("orbicularis03." + sd, f, Quaternion((1, 0, 0), R_(up * 1.6)))
        r.key_q("orbicularis04." + sd, f, Quaternion((1, 0, 0), R_(squint)))

# hero hand helper (armature space for a given scale)
HR = HU["Hero"]; HRIG = RIGS["Hero"]
BODYM = {}
def hand_rest(h, s, f, out=0.08, fwd=-0.02, up=0.0):
    B = h.r.BN; sx = 1 if s == "L" else -1
    out = 0.03 + (out - 0.07) * 0.3; fwd = min(fwd, -0.045); up = up + 0.035      # v003: arms hang close, elbows soft
    if h.r.o.name == "RIG_Hero": out += 0.035; fwd -= 0.01                          # his enlarged hands would brush his thighs
    sh = B["upperarm01." + s].head_local
    W = Vector((sh.x + sx * out, sh.y + fwd, sh.z - 0.43 * (sh.z / 1.031) * 1.0 + up))
    P = Vector((sh.x + sx * 0.2, sh.y + 0.5, sh.z - 0.3)); d = Vector((0, 0, -1)); n = Vector((-sx, 0, 0))
    M = BODYM.get(h)
    if M is not None:
        pos, yaw = M(f); R = Matrix.Rotation(R_(yaw), 3, "Z"); rh = h.root_head
        W = pos + R @ (W - Vector((0, rh.y, 0))); P = pos + R @ (P - Vector((0, rh.y, 0))); d = R @ d; n = R @ n
    h.key_hand(s, f, W, d, n, pole=P)
def hand_w(h, s, f, W, d, n, pole):
    """world-space IK hand target for a rig positioned by its object transform (evaluated at f)"""
    sc.frame_set(f); M = h.r.o.matrix_world.inverted(); R3 = M.to_3x3()
    h.key_hand(s, f, M @ W, (R3 @ d).normalized(), (R3 @ n).normalized(), pole=M @ pole)
def breathe(h, f0, f1, sway=0.012, ph=0.0, base=None, yaw=0.0):
    """weight shift + breathing on the root bone of a standing IK human (feet stay planted)"""
    rh = h.root_head if base is None else base
    for f in range(f0, f1 + 1, 30):
        t = (f + ph * 60) / 60.0
        p = rh + V(sway * math.sin(t * 0.9), 0.004 * math.sin(t * 0.55), -0.006 - 0.004 * math.sin(t * 1.7))
        h.key_root(f, p, yaw=yaw, side=1.5 * math.sin(t * 0.9))
def arms_idle(h, f, out=0.08, fwd=-0.02):
    hand_rest(h, "L", f, out, fwd); hand_rest(h, "R", f, out, fwd)

# ------------------------------------------------------------------ HERO timeline
HPOS = V(-0.3, 2.45, 0.0)
SCALE = [(1, 1.0), (500, 1.0), (560, 1.07), (640, 1.18), (696, 1.26), (800, 1.34), (882, 1.38), (960, 1.47), (1040, 1.56), (1074, 1.6),
         (1476, 1.62), (1700, 1.64), (1860, 1.72), (2340, 1.72)]
for f, s in SCALE:
    HRIG.scale = (s,) * 3; HRIG.keyframe_insert("scale", frame=f)
place("Hero", 1, HPOS, 0); place("Hero", 1481, HPOS, 0, const=True)
# beat 9-10: lying on the bed (head toward +Y end), feet past the foot rail
BED = V(6.9, 0.6, 0.0); MATT_Z = 0.62
place("Hero", 1482, V(BED.x, 1.38 - 1.36 * 1.62, MATT_Z), 0, rx=-90, const=True)
place("Hero", 1857, V(BED.x, 1.38 - 1.36 * 1.64, MATT_Z), 0, rx=-90, const=True)
# beat 11: standing by the theatre door, facing -X
place("Hero", 1858, V(9.45, -0.15, 0.0), -90, const=True)
place("Hero", 1999, V(9.45, -0.15, 0.0), -90, const=True)
# beat 12: dusk field
SIL = V(10.6, 11.6, 0.0)
place("Hero", 2000, SIL, 180 + 8, const=True)
const_keys(HRIG, {1481, 1482, 1857, 1858, 1999, 2000}, "location"); const_keys(HRIG, {1481, 1482, 1857, 1858, 1999, 2000}, "rotation_euler")

# poses: keys every ~20 frames
def hero_pose(f, flex=0, twist=0, side=0, head=(0, 0), jaw_deg=1, up=0, frown=0, squint=0):
    HR.key_spine(f, flex=flex, twist=twist, side=side, head=head); jaw(HR.r, f, jaw_deg); brows(HR.r, f, up, frown, squint)
for f in range(1, 2341, 20):
    pass
# beat 1: stands straight at the rod, chin up hopeful -> deflates
for f, kw in ((1, dict(flex=-4, head=(-10, 0), up=6)), (60, dict(flex=-3, head=(-12, 0), up=8)), (110, dict(flex=6, head=(8, -6), frown=8)),
              (170, dict(flex=8, head=(12, -10), frown=10))):
    hero_pose(f, **kw)
for f in (1, 60, 110, 170): arms_idle(HR, f, 0.06 + 0.01 * (f > 100), -0.02)
# beat 2-3 still (inside), beat 4 strain as he grows
for f, kw in ((372, dict(flex=4, head=(4, 0))), (468, dict(flex=2, head=(0, 0), up=4)), (540, dict(flex=-4, head=(-14, 8), up=10, jaw_deg=5)),
              (620, dict(flex=-6, head=(-10, -8), up=12, jaw_deg=7)), (690, dict(flex=10, head=(18, 0), frown=6))):
    hero_pose(f, **kw)
for f in (372, 468, 540, 620): arms_idle(HR, f, 0.09, -0.03)
# beat 5: left hand flat on the desk, looks at it; right hand at side; then turns to mirror
DESK_TOP = 0.948
def hand_on_desk(f, s_):
    W = V(0.25, 2.33, DESK_TOP + 0.015); Wl = HRIG.matrix_world.inverted() if False else None
    sc_ = s_; Wa = V((W.x - HPOS.x) / sc_, (W.y - HPOS.y) / sc_, W.z / sc_)
    HR.key_hand("L", f, Wa - V(0, 0, 0.03 / sc_), V(0.35, -0.94, 0), V(0, 0, -1), pole=V(0.6, 0.4, 0.9))
for f in (696, 740, 790, 840):
    s_ = dict(SCALE).get(f) or (1.26 + (f - 696) / 186 * 0.12)
    hand_on_desk(f, s_); hand_rest(HR, "R", f, 0.08, -0.02)
for f, kw in ((696, dict(flex=22, side=-10, head=(20, 18), frown=12)), (760, dict(flex=24, side=-10, head=(25, 10), frown=14, jaw_deg=4)),
              (820, dict(flex=10, twist=20, head=(5, 35), up=8, jaw_deg=12)), (870, dict(flex=8, twist=20, head=(3, 30), up=10, jaw_deg=14))):
    hero_pose(f, **kw)
for p in ("tongue00", "tongue01", "tongue02"):
    HR.r.PB[p].scale = (1, 1, 1); HR.r.PB[p].keyframe_insert("scale", frame=800)
    HR.r.PB[p].scale = (1.3, 1.5, 1.3); HR.r.PB[p].keyframe_insert("scale", frame=860)
    HR.r.PB[p].keyframe_insert("scale", frame=875); HR.r.PB[p].scale = (1.15, 1.0, 1.15); HR.r.PB[p].keyframe_insert("scale", frame=900)
# enlargement of hands, feet, jaw (acromegaly) through beats 5-6
for bn, s1 in (("wrist.L", 1.3), ("wrist.R", 1.3), ("foot.L", 1.25), ("foot.R", 1.25), ("jaw", 1.18)):
    pb = HR.r.PB[bn]; pb.scale = (1, 1, 1); pb.keyframe_insert("scale", frame=696)
    pb.scale = (s1,) * 3; pb.keyframe_insert("scale", frame=880)
# beat 6: towers, looks down at officers; arms idle
for f in (882, 940, 1000, 1060): arms_idle(HR, f, 0.08, -0.03)
for f, kw in ((882, dict(flex=4, head=(16, 10), up=4)), (960, dict(flex=6, head=(22, -12))), (1040, dict(flex=8, head=(20, 6), frown=6))):
    hero_pose(f, **kw)
# beat 7: stoop, spine curves
for f, kw in ((1074, dict(flex=8, head=(10, 0))), (1150, dict(flex=24, side=12, head=(12, 0), frown=16, jaw_deg=4)),
              (1240, dict(flex=32, side=16, head=(8, 0), frown=20, jaw_deg=6))):
    hero_pose(f, **kw)
for f in (1074, 1150, 1240): arms_idle(HR, f, 0.1, -0.08)
# beat 8: squints, then cups left hand to left ear
for f, kw in ((1250, dict(flex=26, side=12, head=(14, 0), frown=16, squint=12)), (1330, dict(flex=26, side=10, head=(4, 6), frown=18, squint=22)),
              (1400, dict(flex=24, side=10, head=(4, -18), frown=18, jaw_deg=4)), (1470, dict(flex=24, side=10, head=(2, -22), frown=20))):
    hero_pose(f, **kw)
for f in (1250, 1330, 1370): arms_idle(HR, f, 0.1, -0.08)
B = HR.r.BN
EAR = B["head"].head_local + V(0.085, 0.01, 0.06)
for f in (1400, 1470): hand_rest(HR, "R", f, 0.1, -0.08)
# beat 9-10 lying: arms by sides, relaxed; head turned slightly
for f in (1482, 1600, 1700, 1800, 1857):
    hero_pose(f, flex=0, head=(-4, 6 if f > 1700 else 0), frown=4 if f < 1700 else 0, jaw_deg=2); arms_idle(HR, f, 0.06, 0.02)
# beat 11 standing tall, slight stoop, calm; beat 12 calm
for f in (1858, 1940, 1999): hero_pose(f, flex=10, side=4, head=(10, -16 if f > 1900 else 0)); arms_idle(HR, f, 0.07, -0.04)
for f in (2000, 2150, 2340): hero_pose(f, flex=12, side=4, head=(8, 18 if f > 2100 else 6)); arms_idle(HR, f, 0.07, -0.04)

# ---- growth: feet stay planted in WORLD space (armature scale would slide them outward); small re-plant steps
def hero_scale(f):
    sc.frame_set(f); return HRIG.scale[0]
ANK = {sd: HR.ankle[sd].copy() for sd in "LR"}
plant = {sd: V(HPOS.x + ANK[sd].x, HPOS.y + ANK[sd].y, 0) for sd in "LR"}     # world xy at s = 1
STEPS = [(560, "L"), (650, "R"), (740, "L"), (830, "R"), (920, "L"), (1010, "R"), (1060, "L")]
DUR = 16
for sd in "LR": HR.key_foot(sd, 1, Vector((ANK[sd].x, ANK[sd].y)), 0.0); HR.key_foot(sd, 466, Vector((ANK[sd].x, ANK[sd].y)), 0.0)
for f in list(range(468, 1102, 3)) + [1101]:
    s_ = hero_scale(f)
    for sd in "LR":
        lift = 0.0; P = plant[sd]
        for f0, st in STEPS:
            if st != sd: continue
            tgt = V(HPOS.x + ANK[sd].x * hero_scale(f0 + DUR), HPOS.y + ANK[sd].y * hero_scale(f0 + DUR), 0)
            if f0 <= f < f0 + DUR:
                u = (f - f0) / DUR; P = plant[sd].lerp(tgt, smooth(u)); lift = 0.04 * math.sin(math.pi * u)
            elif f >= f0 + DUR: P = tgt
        xy = Vector(((P.x - HPOS.x) / s_, (P.y - HPOS.y) / s_))
        HR.key_foot(sd, f, xy, 0.0, lift=lift / s_)
for sd in "LR": HR.key_foot(sd, 1110, Vector((ANK[sd].x, ANK[sd].y)), 0.0)
sc.frame_set(1)
# ---- solve the desk hand numerically (palm down, flat, resting on the top) and the ear cup on the evaluated head
def bw(n, f=None):
    if f is not None: sc.frame_set(f)
    return HRIG.matrix_world @ HRIG.pose.bones[n].head
def to_arm(Wworld): return HRIG.matrix_world.inverted() @ Wworld
CANDS = [V(0, 0, -1), V(0, 0, 1), V(1, 0, 0), V(-1, 0, 0), V(0, 1, 0), V(0, -1, 0)]
best = None
for f in (696, 740, 790, 840):
    sc.frame_set(f)
    Wt = to_arm(V(0.12, 2.36, DESK_TOP + 0.032))
    best = None
    for nC in CANDS:
        HR.key_hand("L", f, Wt, V(0.35, -0.94, 0), nC, pole=V(0.6, 0.4, 0.9)); sc.frame_set(f)
        along = bw("finger3-3.L") - bw("wrist.L"); across = bw("finger2-1.L") - bw("finger5-1.L")
        flat = abs(along.normalized().z) + abs(across.normalized().z)
        thumb_ok = bw("finger1-3.L").x < bw("finger5-3.L").x
        score = flat + (0 if thumb_ok else 1.5)
        if best is None or score < best[0]: best = (score, nC)
    HR.key_hand("L", f, Wt, V(0.35, -0.94, 0), best[1], pole=V(0.6, 0.4, 0.9)); sc.frame_set(f)
    lo = min(bw(n).z for n in ("finger2-3.L", "finger3-3.L", "finger4-3.L", "finger3-1.L"))
    Wt2 = to_arm(V(0.12, 2.36, DESK_TOP + 0.032 - (lo - DESK_TOP - 0.008)))
    HR.key_hand("L", f, Wt2, V(0.35, -0.94, 0), best[1], pole=V(0.6, 0.4, 0.9))
    print("DESKHAND", f, best, round(lo, 3))
for f in (1400, 1470):
    sc.frame_set(f); M = HRIG.matrix_world @ HRIG.pose.bones["head"].matrix @ HR.r.BN["head"].matrix_local.inverted()
    earw = M @ V(0.085, -0.03, 1.245); upw = (M.to_3x3() @ V(0, 0, 1)).normalized(); fw = (M.to_3x3() @ V(0, -1, 0)).normalized(); sw = (M.to_3x3() @ V(1, 0, 0)).normalized()
    tgt = to_arm(earw + sw * 0.07 - upw * 0.15 - fw * 0.04)          # wrist just below and outside the ear; fingers rise behind it      # wrist just below/outside the ear, hand cupped up behind it
    HR.key_hand("L", f, tgt, HRIG.matrix_world.inverted().to_3x3() @ (upw * 0.9 - fw * 0.3), HRIG.matrix_world.inverted().to_3x3() @ (fw * 0.8 - sw * 0.2), pole=to_arm(earw + sw * 0.45 - upw * 0.6 + fw * 0.05))
sc.frame_set(1)
# ------------------------------------------------------------------ officers (IK feet, step back as he towers)
O1, O2 = HU["Officer1"], HU["Officer2"]
P1a, P1b = V(-0.86, 2.62, 0), V(-1.3, 1.05, 0)
P2a, P2b = V(-1.15, 1.25, 0), V(-1.9, 0.72, 0)
for h, nm, pa, pb_ in ((O1, "Officer1", P1a, P1b), (O2, "Officer2", P2a, P2b)):
    ya = yaw_to(pa, HPOS); yb = yaw_to(pb_, HPOS)
    BODYM[h] = lambda f, pa=pa, pb_=pb_, ya=ya, yb=yb, bul=(0.42 if h is O1 else 0.0): (pa.lerp(pb_, smooth((f - 890) / 100)) + V(-bul * math.sin(math.pi * smooth((f - 890) / 100)), 0, 0), ya + (yb - ya) * smooth((f - 890) / 100))
    h.key_root(1, pa + V(0, 0, h.root_head.z - 0.01), yaw=ya)
    h.key_foot("L", 1, h.foot_xy("L", pa, ya), ya); h.key_foot("R", 1, h.foot_xy("R", pa, ya), ya)
    h.key_root(880, pa + V(0, 0, h.root_head.z - 0.01), yaw=ya)
    h.key_foot("L", 880, h.foot_xy("L", pa, ya), ya); h.key_foot("R", 880, h.foot_xy("R", pa, ya), ya)
    path = lambda f, pa=pa, pb_=pb_, bul=(0.42 if h is O1 else 0.0): pa.lerp(pb_, smooth((f - 890) / 100)) + V(-bul * math.sin(math.pi * smooth((f - 890) / 100)), 0, 0)
    yfn = lambda f, ya=ya, yb=yb: ya + (yb - ya) * smooth((f - 890) / 100)
    h.walk(path, yfn, 890, 990, stride=0.5, lift=0.06, lean=-4)
    breathe(h, 31, 850, base=pa + V(0, 0, h.root_head.z - 0.01), yaw=ya, ph=1.3 if h is O2 else 0.0)
    breathe(h, 1020, 1446, base=pb_ + V(0, 0, h.root_head.z - 0.02), yaw=yb, ph=0.7 if h is O2 else 2.1)
    h.key_root(1476, pb_ + V(0, 0, h.root_head.z - 0.02), yaw=yb)
    h.key_foot("L", 1476, h.foot_xy("L", pb_, yb), yb); h.key_foot("R", 1476, h.foot_xy("R", pb_, yb), yb)
    for f in range(1, 1477, 30):
        if h is O1 and f < 200: hand_rest(h, "L", f, 0.07, -0.03)    # right hand is on the rod slider (keyed below)
        elif not (886 <= f <= 1476): arms_idle(h, f, 0.07, -0.03)
    for f in range(886, 1000, 6): arms_idle(h, f, 0.1, -0.05)    # hands follow the body through the walk (no lag into the legs)
    for f in range(1000, 1477, 12): arms_idle(h, f, 0.1, -0.05)      # leaning back to look up at him: hands clear of the thighs
    # head shakes (beat 1), look up (beat 6), talk (beat 8)
    for f in range(1, 180, 12):
        h.key_spine(f, flex=4, head=(6, 14 * (1 if (f // 12) % 2 else -1)))
    for f, hd in ((200, (4, 0)), (500, (-6, 0)), (700, (-12, 4)), (900, (-24, -6)), (1000, (-30, 4)), (1100, (-28, 0)), (1300, (-26, 6)), (1476, (-26, -4))):
        h.key_spine(f, flex=-4, head=hd)
    talk(h.r, 1260, 1470, 10, 9); brows(h.r, 1, 0, 10); brows(h.r, 900, 14, 0); brows(h.r, 1300, 6, 6)
    jaw(h.r, 880, 1); jaw(h.r, 930, 10); jaw(h.r, 1000, 6)
# officer1 grips the height rod with his right hand and slides it down to the hero's head height (beat 1)
ROD = V(-0.30, 2.80, 0.0)
to_rod = (ROD - P1a).to_2d().normalized(); side_ = V(-to_rod.y, to_rod.x, 0)
for f, z in ((1, 1.62), (40, 1.58), (90, 1.48), (130, 1.43), (172, 1.43)):
    W = ROD + V(-to_rod.x * 0.05, -to_rod.y * 0.05, z)          # palm against the near face of the rod
    O1.key_hand("R", f, W, V(0, 0, -1) * 0.2 + side_, V(to_rod.x, to_rod.y, 0), pole=W + V(-to_rod.x * 0.25, -to_rod.y * 0.25, -0.45) - side_ * 0.25)
_W = ROD + V(-to_rod.x * 0.3, -to_rod.y * 0.3, 1.12) - side_ * 0.22
O1.key_hand("R", 188, _W, V(0, 0, -1), V(to_rod.x, to_rod.y, 0), pole=_W + V(0, 0, -0.4) - side_ * 0.3)
# ------------------------------------------------------------------ FK extras (clerk writing, recruits waiting, surgeons, nurse)
place("Clerk", 1, V(1.0, 1.6, 0), yaw_to(V(1.0, 1.6, 0), V(0.3, 1.6, 0)))
place("Recruit1", 1, V(-2.85, 1.55, 0), yaw_to(V(-2.85, 1.55, 0), HPOS))
place("Recruit2", 1, V(-2.7, 0.35, 0), yaw_to(V(-2.7, 0.35, 0), HPOS))
CL = HU["Clerk"]; DESK_Z = 0.948
for f in range(1, 1500, 10):
    st = math.sin(f * 0.35)
    hand_w(CL, "R", f, V(0.50 + 0.015 * st, 1.76 + 0.03 * math.sin(f * 0.11), DESK_Z + 0.035 + 0.006 * max(0, st)), V(-1, -0.15, 0), V(0, 0, -1), V(1.0, 2.15, 0.85))
    hand_w(CL, "L", f, V(0.52, 1.42, DESK_Z + 0.033), V(-1, 0.2, 0), V(0, 0, -1), V(1.0, 1.05, 0.85))
    CL.key_spine(f, flex=22 + 2 * math.sin(f * 0.05), twist=3 * math.sin(f * 0.13), head=(22, 4 * math.sin(f * 0.02)))
for f in range(1, 1500, 16):
    for nm, ph in (("Recruit1", 0.0), ("Recruit2", 1.7)):
        r = FK[nm]; arms_down_fk(r, f, out=8, bend=14, sway=3 * math.sin(f * 0.05 + ph))
        body_fk(r, f, flex=3, side=4 * math.sin(f * 0.03 + ph), twist=8 * math.sin(f * 0.021 + ph), head=(-8 if 880 < f < 1300 else 2, 20 * math.sin(f * 0.017 + ph)))
talk(FK["Recruit1"].r if hasattr(FK["Recruit1"], "r") else FK["Recruit1"], 300, 700, 7, 10)
# theatre
SUR = (("Surgeon1", V(6.1, 1.45, 0)), ("Surgeon2", V(7.72, 1.45, 0)), ("Nurse", V(7.55, -0.35, 0)))
PAT = V(6.9, 1.0, 0)
for nm, p in SUR:
    place(nm, 1, p, yaw_to(p, PAT if nm != "Nurse" else V(6.9, -0.35, 0)))
def sterile(h, f, lean=18):
    B = h.r.BN
    for s_, sx in (("L", 1), ("R", -1)):
        sh = B["upperarm01." + s_].head_local
        W = V(sx * 0.12, sh.y - 0.29, sh.z - 0.25); P = V(sh.x + sx * 0.3, sh.y + 0.05, sh.z - 0.45)
        h.key_hand(s_, f, W, V(0, -0.25, 1), V(-sx, 0, 0), pole=P)
for nm in ("Surgeon1", "Surgeon2", "Nurse"):
    h = HU[nm]; ph = {"Surgeon1": 0.0, "Surgeon2": 1.1, "Nurse": 2.3}[nm]
    for f in range(1, 2341, 30):
        if not (nm == "Surgeon1" and 1560 <= f <= 1712) and not (nm == "Nurse" and 1700 <= f <= 1857): sterile(h, f)
        h.key_spine(f, flex=(20 if f < 1712 else 8) + 2 * math.sin(f * 0.05 + ph), twist=4 * math.sin(f * 0.03 + ph), head=(24 if f < 1712 else 8, 8 * math.sin(f * 0.02 + ph)))
    breathe(h, 1, 2340, sway=0.008, ph=ph)
# Surgeon1 lays his right hand on the drape at the patient's shoulder (contact, palm down)
S1 = HU["Surgeon1"]
for f in (1575, 1600, 1650, 1700, 1712):
    sc.frame_set(f); sh_w = HRIG.matrix_world @ HRIG.pose.bones["upperarm01.R"].head
    tgt = sh_w + V(0, -0.02, 0.075)
    hand_w(S1, "R", f, tgt, (PAT - V(6.1, 1.45, 0)).normalized(), V(0, 0, -1), tgt + V(0.05, 0.35, -0.45))
    if f >= 1575: hand_w(S1, "L", f, V(6.32, 1.25, 1.12), V(0.6, -0.6, 0.3), V(0.3, 0.3, -1), V(6.0, 1.2, 0.8))
# Nurse tucks the blanket over his shins with both hands (beat 10)
NU = HU["Nurse"]
for i, f in enumerate([1690] + list(range(1700, 1858, 18)) + [1857]):
    sc.frame_set(f)
    for s_, ln, dx in (("L", "lowerleg01.L", 0.0), ("R", "lowerleg01.R", 0.0)):
        lw = HRIG.matrix_world @ HRIG.pose.bones[ln].head
        wide = 0.1 if f in (1690, 1857) else 0.0
        tgt = lw + V(0.05 + wide, (0.12 + wide) if s_ == "L" else -(0.12 + wide), 0.11 + 0.01 * math.sin(i * 1.7) + wide * 1.5)
        hand_w(NU, s_, f, tgt, V(-1, 0, -0.2), V(0, 0, -1), tgt + V(0.35, 0.0, -0.4))
breathe(HR, 1, 1470, sway=0.008, ph=0.4); breathe(HR, 1858, 1999, sway=0.008, ph=0.9); breathe(HR, 2000, 2340, sway=0.01, ph=1.7)
# beat 11 normal man looks up at the hero; beat 12 young self
Nm = HU["Normal"]; PN = V(9.4, -2.55, 0); yN = yaw_to(PN, V(8.0, -1.4, 0)) + 10
BODYM[Nm] = lambda f: (PN, yN)
Nm.key_root(1, PN + V(0, 0, Nm.root_head.z - 0.01), yaw=yN)
Nm.key_foot("L", 1, Nm.foot_xy("L", PN, yN), yN); Nm.key_foot("R", 1, Nm.foot_xy("R", PN, yN), yN)
for f in range(1, 2341, 40): arms_idle(Nm, f, 0.07, -0.03); Nm.key_spine(f, flex=-3, head=(-14, -28 + 6 * math.sin(f * 0.05)))
breathe(Nm, 1, 2340, base=PN + V(0, 0, Nm.root_head.z - 0.01), yaw=yN, ph=0.5)
Yg = HU["Young"]; PY = SIL + V(-0.85, 0.05, 0); yY = 180 - 8
BODYM[Yg] = lambda f: (PY, yY)
Yg.key_root(1, PY + V(0, 0, Yg.root_head.z - 0.01), yaw=yY)
Yg.key_foot("L", 1, Yg.foot_xy("L", PY, yY), yY); Yg.key_foot("R", 1, Yg.foot_xy("R", PY, yY), yY)
for f in range(1, 2341, 40): arms_idle(Yg, f, 0.07, -0.03); Yg.key_spine(f, flex=-2, head=(-10 if f > 2150 else -4, -24 if f > 2150 else -4))
breathe(Yg, 1, 2340, base=PY + V(0, 0, Yg.root_head.z - 0.01), yaw=yY, ph=2.2)
for nm, rng in (("Officer1", [(1, 1476)]), ("Officer2", [(1, 1476)]), ("Clerk", [(1, 1476)]), ("Recruit1", [(1, 1476)]), ("Recruit2", [(1, 1476)]),
                ("Surgeon1", [(1477, 1857)]), ("Surgeon2", [(1477, 1857)]), ("Nurse", [(1477, 1857)]), ("Normal", [(1858, 1999)]), ("Young", [(2000, 2340)])):
    for m_ in meshes_of(RIGS[nm]): vis(m_, rng)

# ------------------------------------------------------------------ x-ray body, brain, spine, hormone stream
hero_meshes = meshes_of(HRIG)
body = OB["Hero.body"]
xr = body.copy(); xr.data = body.data.copy(); xr.name = "Hero_Xray"; body.users_collection[0].objects.link(xr)
xm = bpy.data.materials.new("M_Xray"); xm.use_nodes = True; nt = xm.node_tree; nt.nodes.clear()
o_ = nt.nodes.new("ShaderNodeOutputMaterial"); lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.35
em = nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (0.35, 0.85, 1.0, 1)
mth = nt.nodes.new("ShaderNodeMath"); mth.operation = "MULTIPLY"; mth.inputs[1].default_value = 2.2
nt.links.new(lw.outputs["Facing"], mth.inputs[0]); nt.links.new(mth.outputs[0], em.inputs[1])
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); ad_ = nt.nodes.new("ShaderNodeAddShader")
nt.links.new(tr.outputs[0], ad_.inputs[0]); nt.links.new(em.outputs[0], ad_.inputs[1]); nt.links.new(ad_.outputs[0], o_.inputs[0])
xr.data.materials.clear(); xr.data.materials.append(xm)
for md in [m for m in xr.modifiers if m.type == "MASK" and m.name.startswith("Delete")]: xr.modifiers.remove(md)
XRAY = [(372, 500), (1074, 1262)]
vis(xr, XRAY)
for m_ in hero_meshes:
    hide_ranges(m_, [(181, 470), (1080, 1255), (1658, 1712)])
BR = OB["Brain"]; BR.parent = HRIG; BR.parent_type = "BONE"; BR.parent_bone = "head"
hb = HR.r.BN["head"]; BRAIN_LOCAL = V(0.0, -0.035, 0.085)        # in head-bone space (y along bone)
BR.matrix_parent_inverse = Matrix.Identity(4)
BR.location = V(0, -0.148, 0.0); BR.scale = (0.84,) * 3
BR.rotation_euler = (R_(-90), 0, 0)
brain_objs = [BR] + list(BR.children_recursive)
for o in brain_objs:
    if o.type == "MESH": vis(o, [(181, 500), (1658, 1712)])
PIT = OB["Pituitary"]; TUM = OB["Tumour"]
for o, off in ((PIT, V(0, -0.014, 0.036)), (TUM, V(0, -0.017, 0.033))):
    o.parent = BR; o.location = off; o.rotation_euler = (R_(90), 0, 0)
    vis(o, [(181, 500), (1658, 1712)])
tb = TUM.data.materials[0].node_tree.nodes["Principled BSDF"]
for f, s, e in ((181, 0.25, 0.0), (250, 0.5, 0.5), (300, 0.9, 1.5), (360, 1.3, 3.0), (420, 1.4, 4.0), (500, 1.4, 3.0), (1658, 1.4, 4.0), (1690, 1.4, 2.0)):
    TUM.scale = (s,) * 3; TUM.keyframe_insert("scale", frame=f)
    tb.inputs["Emission Strength"].default_value = e; tb.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
for f in range(260, 500, 14):  # pulse
    TUM.scale = (TUM.scale[0] * 1.06,) * 3
# tumour is lifted out by forceps (beat 9)
FORC = []
for i, sx in enumerate((1, -1)):
    me = bpy.data.meshes.new(f"Forceps{i}"); bm = bmesh.new()
    prof = [(0.0, 0.0), (0.004, 0.03), (0.007, 0.08), (0.008, 0.14)]
    vs = []
    for (x, z) in prof:
        for dx, dy in ((-0.0012, -0.0009), (0.0012, -0.0009), (0.0012, 0.0009), (-0.0012, 0.0009)):
            vs.append(bm.verts.new((sx * x + dx, dy, z)))
    for k in range(len(prof) - 1):
        for j in range(4):
            a1, a2 = vs[k * 4 + j], vs[k * 4 + (j + 1) % 4]; b1, b2 = vs[(k + 1) * 4 + (j + 1) % 4], vs[(k + 1) * 4 + j]
            bm.faces.new((a1, a2, b1, b2))
    bm.to_mesh(me); bm.free()
    fo = bpy.data.objects.new(f"Forceps{i}", me); BR.users_collection[0].objects.link(fo)
    mm = bpy.data.materials.new("M_Steel"); mm.use_nodes = True; b = mm.node_tree.nodes["Principled BSDF"]
    b.inputs["Metallic"].default_value = 1.0; b.inputs["Roughness"].default_value = 0.22; b.inputs["Base Color"].default_value = (0.75, 0.75, 0.76, 1)
    me.materials.append(mm); sub = fo.modifiers.new("s", "SUBSURF"); sub.levels = 1; sub.render_levels = 2
    fo.parent = TUM; fo.location = (sx * 0.003, 0, 0.002); fo.rotation_euler = (0, 0, 0)
    vis(fo, [(1658, 1712)]); FORC.append(fo)
TUM.keyframe_insert("location", frame=1680)
TUM.location = TUM.location + V(0, 0.0, -0.06); TUM.keyframe_insert("location", frame=1708)
# spine inside the x-ray torso, bends (scoliosis)
SP = OB["Spine"]; SP.parent = HRIG; SP.location = (0, 0.035, 0.6); SP.rotation_euler = (0, 0, 0); SP.scale = (0.95,) * 3
spm = [o for o in SP.children_recursive if o.type == "MESH"]
for o in spm:
    vis(o, [(1074, 1262), (372, 500)])
    md = o.modifiers.new("bend", "SIMPLE_DEFORM"); md.deform_method = "BEND"; md.deform_axis = "Y"; md.origin = SP
    md.angle = 0.0; md.keyframe_insert("angle", frame=1090); md.angle = R_(55); md.keyframe_insert("angle", frame=1220)
# hormone stream: glowing particles from the pituitary down vessels (in hero armature space)
Bn = HR.r.BN
def bh(n): return Bn[n].head_local.copy()
ROUTES = [[bh("head") + V(0, -0.03, 0.02), bh("neck01"), bh("spine03"), bh("shoulder01." + s), bh("upperarm01." + s), bh("lowerarm01." + s), bh("wrist." + s), bh("finger3-1." + s)] for s in "LR"] + \
         [[bh("head") + V(0, -0.03, 0.02), bh("neck01"), bh("spine03"), bh("spine01"), bh("pelvis." + s), bh("upperleg01." + s), bh("lowerleg01." + s), bh("foot." + s), bh("toe1-1." + s)] for s in "LR"]
pm = bpy.data.materials.new("M_Hormone"); pm.use_nodes = True; nt = pm.node_tree; nt.nodes.clear()
o_ = nt.nodes.new("ShaderNodeOutputMaterial"); e_ = nt.nodes.new("ShaderNodeEmission"); e_.inputs[0].default_value = (1.0, 0.62, 0.15, 1); e_.inputs[1].default_value = 25
nt.links.new(e_.outputs[0], o_.inputs[0])
pmesh = bpy.data.meshes.new("HormoneDot"); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.0045); bm.to_mesh(pmesh); bm.free()
pmesh.materials.append(pm)
def route_pt(rt, u):
    L = [0.0]
    for p, q in zip(rt, rt[1:]): L.append(L[-1] + (q - p).length)
    d = u * L[-1]
    for i in range(len(rt) - 1):
        if d <= L[i + 1]: return rt[i].lerp(rt[i + 1], (d - L[i]) / max(1e-6, L[i + 1] - L[i]))
    return rt[-1]
for k in range(110):
    o = bpy.data.objects.new(f"Hormone{k:03d}", pmesh); xr.users_collection[0].objects.link(o); o.parent = HRIG
    rt = ROUTES[k % 4]; t0 = 372 + random.randint(0, 50); dur = random.randint(50, 80); jit = V(random.gauss(0, 0.012), random.gauss(0, 0.01), random.gauss(0, 0.01))
    for f in range(t0, min(t0 + dur, 500) + 1, 4):
        o.location = route_pt(rt, (f - t0) / dur) + jit; o.keyframe_insert("location", frame=f)
    vis(o, [(t0, min(t0 + dur, 500))])

# ------------------------------------------------------------------ camera
cam_d = bpy.data.cameras.new("CAM_Film"); cam_d.sensor_fit = "AUTO"; cam_d.clip_start = 0.004; cam_d.clip_end = 200
cam = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(cam); sc.camera = cam
aim = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(aim); aim.hide_render = True
tt = cam.constraints.new("TRACK_TO"); tt.target = aim; tt.track_axis = "TRACK_NEGATIVE_Z"; tt.up_axis = "UP_Y"
cam_d.dof.use_dof = True; cam_d.dof.focus_object = aim; cam_d.dof.aperture_fstop = 4.0
# evaluated head / brain helpers (camera keys follow the real animated rig)
_HB = HR.r.BN["head"]; _HINV = _HB.matrix_local.inverted()
def head_pt(f, rest_pt):
    sc.frame_set(f); M = HRIG.matrix_world @ HRIG.pose.bones["head"].matrix @ _HINV
    return M @ Vector(rest_pt)
EYES_R = (0.0, -0.13, 1.238); EARL_R = (0.08, -0.03, 1.245); EARR_R = (-0.08, -0.03, 1.245); HC_R = (0.0, -0.03, 1.26); TOP_R = (0, -0.03, 1.36)
def head_frame(f):
    c = head_pt(f, HC_R); e = head_pt(f, EYES_R); l = head_pt(f, EARL_R); r_ = head_pt(f, EARR_R); t = head_pt(f, TOP_R)
    return c, (e - c).normalized(), (l - r_).normalized(), (t - c).normalized(), l, e
def obj_w(f, o, off=(0, 0, 0)):
    sc.frame_set(f); return o.matrix_world @ Vector(off)
TUMO = OB["Tumour"]; BRO = OB["Brain"]
HEAD0 = obj_w(240, BRO, (0, 0, 0.05)); PITW = obj_w(300, TUMO)
c8a, f8a, s8a, u8a, ear8a, eye8a = head_frame(1275); c8b, f8b, s8b, u8b, ear8b, eye8b = head_frame(1335)
c8c, f8c, s8c, u8c, ear8c, eye8c = head_frame(1385); c8d, f8d, s8d, u8d, ear8d, eye8d = head_frame(1445)
OFFS = V(-1.35, 0.72, 1.62)
c9, f9, s9, u9, ear9, eye9 = head_frame(1640); c9b, f9b, s9b, u9b, _, _ = head_frame(1668)
BR9 = obj_w(1690, BRO, (0, 0, 0.05)); TU9 = obj_w(1690, TUMO)
LH = c9
c11, f11, s11, u11, _, _ = head_frame(1900)
DYN = [(1275, eye8a + f8a * 0.10, OFFS, 28), (1335, eye8b + f8b * 0.12 + u8b * 0.02, OFFS, 30),
       (1385, ear8c + s8c * 0.5 + f8c * 0.3 + u8c * 0.05, ear8c - u8c * 0.04, 32), (1445, ear8d + s8d * 0.6 + f8d * 0.4 + u8d * 0.08, ear8d - u8d * 0.06 + f8d * 0.05, 30),
       (1640, c9 + f9 * 0.42 + s9 * 0.12 - u9 * 0.05, c9 + f9 * 0.06, 30), (1654, c9b + (f9b + u9b * 0.42).normalized() * 0.26, c9b, 32), (1660, c9b + (f9b + u9b * 0.42).normalized() * 0.16, c9b, 40), (1666, c9b + (f9b + u9b * 0.3).normalized() * 0.14 + s9b * 0.04, c9b, 38), (1676, c9b + f9b * 0.14 + s9b * 0.1, c9b, 36),
       (1690, BR9 + s9b * 0.16 + f9b * 0.06, TU9, 40), (1708, BR9 + s9b * 0.12 - u9b * 0.05 + f9b * 0.08, TU9, 45), (1718, c9 + f9 * 0.45 + u9 * 0.15 + s9 * 0.1, c9, 30)]
sc.frame_set(1)
KEYS = [  # frame, cam, aim, lens
    (1, V(1.25, -0.55, 2.75), V(-0.3, 2.3, 1.15), 26), (45, V(0.55, 0.35, 1.95), V(-0.3, 2.4, 1.05), 28),
    (95, V(-0.05, 1.1, 1.25), V(-0.3, 2.45, 1.22), 32), (140, V(-0.35, 1.72, 1.3), V(-0.3, 2.4, 1.25), 38),
    (170, V(-0.56, 2.28, 1.21), V(-0.3, 2.37, 1.205), 45), (180, V(-0.392, 2.352, 1.205), V(-0.3, 2.375, 1.205), 45),
    (190, V(-0.335, 2.37, 1.215), V(-0.3, 2.39, 1.23), 32), (240, V(-0.5, 2.25, 1.33), HEAD0, 35),
    (300, V(-0.36, 2.16, 1.17), PITW, 45), (355, V(-0.29, 2.22, 1.19), PITW, 55),
    (380, V(-0.22, 2.08, 1.2), PITW + V(0, 0, -0.01), 40), (420, V(-0.05, 1.55, 1.05), V(-0.3, 2.45, 0.9), 28),
    (462, V(-0.15, 1.0, 0.95), V(-0.3, 2.45, 0.62), 24), (510, V(0.55, 0.55, 0.95), V(-0.75, 2.5, 1.0), 22),
    (565, V(0.85, 0.25, 1.25), V(-0.85, 2.5, 1.2), 22), (625, V(0.35, 0.15, 1.6), V(-0.6, 2.5, 1.45), 24),
    (690, V(0.05, 1.05, 1.4), V(0.1, 2.25, 0.95), 30), (740, V(0.1, 1.75, 1.22), V(0.12, 2.36, 0.96), 40),
    (790, V(-0.05, 1.6, 0.45), V(-0.25, 2.42, 0.12), 32), (815, V(-0.42, 1.72, 1.35), V(0.2, 2.6, 1.4), 30), (845, V(-0.22, 2.64, 1.97), V(2.8, 2.98, 1.72), 38),
    (880, V(-0.2, 1.0, 1.3), V(-0.35, 2.2, 1.5), 26), (920, V(1.5, -0.1, 0.45), V(-0.3, 2.0, 1.5), 22),
    (975, V(0.35, -0.85, 0.42), V(-0.35, 2.0, 1.6), 22), (1030, V(-1.45, -0.45, 0.5), V(-0.3, 2.1, 1.6), 22),
    (1075, V(-0.75, 0.75, 1.45), V(-0.3, 2.35, 1.4), 26), (1120, V(-0.95, 0.95, 1.3), V(-0.3, 2.45, 1.15), 28),
    (1175, V(-0.45, 1.2, 1.25), V(-0.3, 2.45, 1.1), 30), (1235, V(0.15, 1.35, 1.55), V(-0.3, 2.45, 1.3), 28),
            (1466, V(0.75, 1.95, 2.0), V(1.6, 3.1, 1.85), 28), (1488, V(2.45, 1.62, 2.13), V(5.0, 1.2, 1.6), 26), (1494, V(3.44, 1.44, 2.2), V(6.0, 1.0, 1.4), 24),
    (1498, V(3.95, 1.36, 2.26), V(6.5, 0.9, 1.3), 24), (1540, V(4.55, 1.25, 2.4), V(6.9, 0.6, 0.9), 24),
    (1595, V(5.8, -0.65, 2.6), V(6.9, 0.6, 0.85), 26),         (1740, V(6.3, 1.2, 1.35), V(6.9, 0.6, 0.72), 28),
    (1790, V(6.1, 0.5, 1.45), V(6.9, -0.05, 0.7), 26), (1845, V(5.7, -1.25, 1.55), V(6.9, -0.45, 0.6), 26),
    (1868, V(6.0, -1.25, 1.45), V(9.45, -1.0, 1.4), 22), (1930, V(6.2, -0.5, 0.8), V(9.45, -1.0, 1.55), 22),
    (1950, V(7.2, -0.1, 1.75), V(7.2, 3.1, 1.95), 24), (1972, V(7.4, 1.3, 2.2), V(7.1, 3.1, 2.0), 24), (1998, V(7.1, 3.0, 2.45), V(7.3, 6.0, 1.8), 26),
    (2035, V(8.3, 5.2, 3.2), V(8.6, 7.0, 0.1), 28), (2100, V(8.9, 6.1, 2.2), V(10.2, 11.5, 1.2), 30),
    (2180, V(9.25, 6.9, 1.55), V(10.2, 11.6, 1.25), 35), (2260, V(9.6, 7.3, 2.35), V(10.2, 11.6, 1.35), 32),
    (2340, V(9.75, 7.45, 2.8), V(10.2, 11.6, 1.45), 32)]
KEYS = sorted(KEYS + DYN, key=lambda k: k[0])
fc_ = catmull([(f, c) for f, c, a_, l in KEYS]); fa_ = catmull([(f, a_) for f, c, a_, l in KEYS]); fl_ = catmull([(f, float(l)) for f, c, a_, l in KEYS])
for f in list(range(1, 2341, 2)) + [2340]:
    cam.location = fc_(f); cam.keyframe_insert("location", frame=f)
    aim.location = fa_(f); aim.keyframe_insert("location", frame=f)
    cam_d.lens = fl_(f); cam_d.keyframe_insert("lens", frame=f)
# POV blur (beat 8): focus empty follows the aim, but sits 0.25 m in front of the lens during the POV
foc = bpy.data.objects.new("CAM_Focus", None); sc.collection.objects.link(foc); foc.hide_render = True
cam_d.dof.focus_object = foc
for f in list(range(1, 2341, 4)) + [2340]:
    p_ = fa_(f)
    w = smooth((f - 1268) / 22) * (1 - smooth((f - 1352) / 28))
    if w > 0:
        cpos = fc_(f); near = cpos + (p_ - cpos).normalized() * 0.25; p_ = p_.lerp(near, w)
    foc.location = p_; foc.keyframe_insert("location", frame=f)
for f, fs in ((1, 8.0), (180, 8.0), (181, 22.0), (500, 22.0), (501, 8.0), (1262, 8.0), (1292, 1.4), (1335, 1.4), (1365, 8.0), (1657, 8.0), (1658, 22.0), (1712, 22.0), (1713, 8.0)):
    cam_d.dof.aperture_fstop = fs; cam_d.dof.keyframe_insert("aperture_fstop", frame=f)

# camera-attached cutaway card (teal->navy gradient), alpha keyed
XB = OB["XBack"]; card = XB
me = bpy.data.meshes.new("CutCard"); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.0); bm.to_mesh(me); bm.free()
cc = bpy.data.objects.new("CutCard", me); XB.users_collection[0].objects.link(cc); cc.parent = cam
cm = XB.data.materials[0].copy(); me.materials.append(cm)
_rp = next(n for n in cm.node_tree.nodes if n.type == "VALTORGB"); _rp.color_ramp.elements[0].color = (0.80, 0.93, 1.0, 1); _rp.color_ramp.elements[1].color = (0.08, 0.55, 0.93, 1); _rp.color_ramp.elements[1].position = 1.0
cm.node_tree.nodes["Map Range"].inputs[1].default_value = -0.5; cm.node_tree.nodes["Map Range"].inputs[2].default_value = 0.5
sep_ = cm.node_tree.nodes["Separate XYZ"]; cm.node_tree.links.new(sep_.outputs[1], cm.node_tree.nodes["Map Range"].inputs[0])
cc.visible_shadow = False
CARD = [(180, 0.0, 0.6), (181, 1.0, 0.6), (186, 1.0, 0.55), (360, 1.0, 0.5), (380, 1.0, 0.5), (420, 1.0, 1.15), (462, 1.0, 1.62), (470, 1.0, 1.62), (500, 0.0, 1.62),
        (1074, 0.0, 1.85), (1090, 1.0, 1.85), (1240, 1.0, 1.85), (1262, 0.0, 1.85), (1657, 0.0, 0.22), (1658, 1.0, 0.22), (1700, 1.0, 0.24), (1712, 0.0, 0.3)]
mixn = cm.node_tree.nodes["FADE"]
for f, al, dist in CARD:
    mixn.inputs[0].default_value = al; mixn.inputs[0].keyframe_insert("default_value", frame=f)
    cc.location = (0, 0, -dist); cc.scale = (dist * 1.3, dist * 2.2, 1); cc.keyframe_insert("location", frame=f); cc.keyframe_insert("scale", frame=f)
vis(cc, [(181, 500), (1074, 1262), (1658, 1712)])
bpy.data.objects.remove(XB, do_unlink=True)
for o in [o for o in OB if "stash" in o.name.lower()]: bpy.data.objects.remove(o, do_unlink=True)
# light for the cutaway (studio key/rim parented to camera)
for nm, loc, e, colr in (("Cut_Key", (0.4, 0.5, 0.2), 6.0, (1.0, 0.92, 0.85)), ("Cut_Rim", (-0.3, 0.4, -0.6), 9.0, (0.4, 0.85, 1.0))):
    l = bpy.data.lights.new(nm, "AREA"); l.energy = e; l.size = 0.3; l.color = colr
    lo = bpy.data.objects.new(nm, l); sc.collection.objects.link(lo); lo.parent = cam; lo.location = loc
    tc = lo.constraints.new("TRACK_TO"); tc.target = aim; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
    l.energy = 0.0; l.keyframe_insert("energy", frame=1)
    for f0, f1 in ((181, 500), (1074, 1262), (1658, 1712)):
        l.energy = 0.0; l.keyframe_insert("energy", frame=f0 - 1); l.energy = e; l.keyframe_insert("energy", frame=f0)
        l.keyframe_insert("energy", frame=f1); l.energy = 0.0; l.keyframe_insert("energy", frame=f1 + 1)

# ------------------------------------------------------------------ sun: day in the office, time-lapse sweep in beat 4/6, dusk at the end
sun = OB["Sun"]
def sun_dir(az, el):
    d = Vector((math.cos(R_(el)) * math.sin(R_(az)), -math.cos(R_(el)) * math.cos(R_(az)), math.sin(R_(el))))
    return d.to_track_quat("Z", "Y").to_euler()
for f, az, el, e, colr in ((1, 170, 40, 3.5, (1, 0.93, 0.82)), (468, 170, 40, 3.5, (1, 0.93, 0.82)), (560, 120, 20, 2.0, (1, 0.7, 0.45)),
                           (620, 220, 30, 3.0, (1, 0.9, 0.8)), (696, 170, 42, 3.5, (1, 0.93, 0.82)), (930, 120, 15, 2.0, (1, 0.7, 0.5)),
                           (990, 210, 25, 2.2, (0.85, 0.9, 1.0)), (1050, 170, 40, 3.5, (1, 0.93, 0.82)), (1860, 170, 30, 2.2, (1, 0.85, 0.7)),
                           (1990, 175, 8, 4.5, (1, 0.55, 0.3)), (2340, 178, 4, 4.5, (1, 0.5, 0.25))):
    sun.rotation_euler = sun_dir(az, el); sun.keyframe_insert("rotation_euler", frame=f)
    sun.data.energy = e; sun.data.color = colr; sun.data.keyframe_insert("energy", frame=f); sun.data.keyframe_insert("color", frame=f)
bg = sc.world.node_tree.nodes["Background"]
dk = sc.world.node_tree.nodes["DUSK"]
for f, v in ((1, 0.0), (1990, 0.0), (2015, 1.0)):
    dk.inputs[0].default_value = v; dk.inputs[0].keyframe_insert("default_value", frame=f)
for f, s in ((1, 1.0), (1980, 1.0), (2015, 0.45), (2340, 0.3)):
    bg.inputs[1].default_value = s; bg.inputs[1].keyframe_insert("default_value", frame=f)
# office / theatre lights off when not needed (render speed)
for nm, rng in (("Off_Sconce", [(1, 1525)]), ("Off_Key", [(1, 1525)]), ("Off_Fill", [(1, 1525)]), ("Th_Key", [(1477, 2010)]), ("Th_Fill", [(1477, 2010)])):
    vis(OB[nm], rng)
# seasons in the window (beat 4 time-lapse + beat 6): leaves green -> autumn -> bare/frosted -> green
for m in bpy.data.materials:
    if "leaves" in m.name.lower() and m.node_tree:
        nt = m.node_tree; b = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if not b or not b.inputs["Base Color"].links: continue
        src = b.inputs["Base Color"].links[0].from_socket
        hs = nt.nodes.new("ShaderNodeHueSaturation"); nt.links.new(src, hs.inputs["Color"]); nt.links.new(hs.outputs[0], b.inputs["Base Color"])
        for f, hue, sat, val in ((1, 0.5, 1.0, 1.0), (520, 0.5, 1.0, 1.0), (570, 0.42, 1.4, 1.1), (620, 0.5, 0.15, 1.9), (680, 0.5, 1.0, 1.0),
                                 (900, 0.5, 1.0, 1.0), (940, 0.41, 1.5, 1.1), (985, 0.5, 0.1, 2.2), (1030, 0.52, 1.1, 1.0)):
            hs.inputs["Hue"].default_value = hue; hs.inputs["Saturation"].default_value = sat; hs.inputs["Value"].default_value = val
            for k in ("Hue", "Saturation", "Value"): hs.inputs[k].keyframe_insert("default_value", frame=f)
# dust motes drifting in the window light (office) and theatre
dm = bpy.data.materials.new("M_Dust"); dm.use_nodes = True; db = dm.node_tree.nodes["Principled BSDF"]
db.inputs["Base Color"].default_value = (0.9, 0.85, 0.75, 1); db.inputs["Emission Color"].default_value = (1, 0.9, 0.7, 1); db.inputs["Emission Strength"].default_value = 1.5
dmesh = bpy.data.meshes.new("DustDot"); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.0025); bm.to_mesh(dmesh); bm.free(); dmesh.materials.append(dm)
for k in range(160):
    o = bpy.data.objects.new(f"Dust{k:03d}", dmesh); sc.collection.objects.link(o)
    room = k % 2
    base = V(random.uniform(-2.5, 2.5), random.uniform(-0.5, 2.9), random.uniform(0.3, 2.8)) if room == 0 else V(random.uniform(4.5, 9.5), random.uniform(-2.5, 2.8), random.uniform(0.4, 2.8))
    ph = random.uniform(0, 6.28); sp = random.uniform(0.004, 0.01)
    for f in range(1, 2341, 60):
        o.location = base + V(0.25 * math.sin(f * sp + ph), 0.2 * math.cos(f * sp * 0.7 + ph), -0.0004 * f % 0.6 + 0.1 * math.sin(f * sp * 1.3)); o.keyframe_insert("location", frame=f)
    vis(o, [(1, 1525)] if room == 0 else [(1477, 2000)])
# fly-through: the shared office/theatre wall is not rendered while the camera passes it (no blank plaster frames)
for nm in ("Off_WallR", "Off_WainR", "Off_RailR", "Th_WallL"):
    hide_ranges(OB[nm], [(1482, 1497)])
# hide helper empties from render
for o in OB:
    if o.type == "EMPTY": o.hide_render = True
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
