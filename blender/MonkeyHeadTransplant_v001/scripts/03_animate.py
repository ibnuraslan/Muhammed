"""Animation + camera for MonkeyHeadTransplant (blocking pass).
blender -b build/scene.blend --python scripts/03_animate.py -- <out.blend>"""
import sys, os, math, json
import bpy
from mathutils import Vector, Matrix, Quaternion
OUT = sys.argv[sys.argv.index("--") + 1]
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
sc = bpy.context.scene
V = lambda *a: Vector(a)
D = bpy.data.objects
FPS = 60
def fr(t): return 1 + round(t * FPS)
BEATS = [(1, 0.0, "In 1970, a surgeon removed the head"), (2, 4.3, "attached it to the body of another one"),
         (3, 6.5, "carefully joining the tissue in the neck"), (4, 11.2, "incredibly, the monkey survived"),
         (5, 14.8, "could still see and hear"), (6, 17.1, "spinal cord couldn't be reconnected"),
         (7, 20.1, "couldn't move its body at all"), (8, 23.2, "technically a success"), (9, 26.0, "only lived for a few more days")]
B = {n: fr(t) for n, t, _ in BEATS}
json.dump([{"beat": n, "frame": fr(t), "first_words": w} for n, t, w in BEATS],
          open(os.path.join(HERE, "..", "beats.json"), "w"), indent=1)

def keyv(obj, path, f, val, idx=-1):
    setattr(obj, path, val) if idx < 0 else getattr(obj, path).__setitem__(idx, val)
    obj.keyframe_insert(path, frame=f, index=idx)
def node_key(mat_name, node, f, v):
    n = bpy.data.materials[mat_name].node_tree.nodes[node]
    n.outputs[0].default_value = v; n.outputs[0].keyframe_insert("default_value", frame=f)
def all_mats_with(node):
    return [m.name for m in bpy.data.materials if m.use_nodes and node in m.node_tree.nodes]
def hide_keys(obj, keys):
    for f, h in keys:
        obj.hide_render = h; obj.keyframe_insert("hide_render", frame=f)
        obj.hide_viewport = h; obj.keyframe_insert("hide_viewport", frame=f)
def set_const(obj):
    ad = obj.animation_data
    if not ad or not ad.action: return
    for layer in getattr(ad.action, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    if fc.data_path in ("hide_render", "hide_viewport"):
                        for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"

# ------------------------------------------------------------------ key places
rootB = D["MonkeyRootB"]; rootA = D["MonkeyRootA"]; head = D["MK_Head"]; nref = D["NeckRef"]
M_LIE2 = rootB.matrix_world.copy(); M_LIE1 = rootA.matrix_world.copy()
NC = nref.location.copy()                                    # model-space neck centre
NA = M_LIE1 @ NC; NB = M_LIE2 @ NC
EYEMID = V(-0.0844, -0.4668, 0.2635 + 0.181)
FB = M_LIE2 @ EYEMID
CH = D["Chair"].location.copy()
SEAT = 0.409
M_CHAIR = Matrix.Translation(CH + V(0.0, 0.26, SEAT + 0.004)) @ Matrix.Rotation(math.radians(-7), 4, "X") @ Matrix.Rotation(math.radians(5), 4, "Y")
print("NA", NA, "NB", NB, "FB", FB)
# monkey B root: table 2 -> chair while the x-ray void hides the world (camera rides along rigidly)
W0, W1 = 1068, 1172
def M_root(f):
    t = smooth((f - W0) / (W1 - W0))
    if t <= 0: return M_LIE2
    if t >= 1: return M_CHAIR
    l0, q0, _ = M_LIE2.decompose(); l1, q1, _ = M_CHAIR.decompose()
    return Matrix.Translation(l0.lerp(l1, t)) @ q0.slerp(q1, t).to_matrix().to_4x4()
for f in list(range(W0 - 2, W1 + 3, 2)):
    M = M_root(f); l, q, _ = M.decompose()
    rootB.location = l; rootB.keyframe_insert("location", frame=f)
    rootB.rotation_quaternion = q; rootB.keyframe_insert("rotation_quaternion", frame=f)

# ------------------------------------------------------------------ head path: on A until lifted, carried to B, seated
L_A = M_LIE2.inverted() @ M_LIE1          # head local (B frame) when sitting on body A
L_B = Matrix.Identity(4)
HEAD_KEYS = [(1, 0.0, 0.0, 0.0), (250, 0.0, 0.0, 0.0), (262, 0.0, 0.0, 0.035), (285, 0.15, 0.0, 0.13), (315, 0.55, 0.0, 0.16),
             (340, 0.92, 0.0, 0.07), (356, 1.0, 0.0, 0.012), (366, 1.0, 0.0, -0.002), (374, 1.0, 0.0, 0.0)]
fu = pchip([(f, u) for f, u, _, _ in HEAD_KEYS]); fz = pchip([(f, z) for f, _, _, z in HEAD_KEYS])
def head_world(f):
    u = fu(f); z = fz(f)
    lA = M_LIE1; lB = M_LIE2
    p = lA.translation.lerp(lB.translation, u) + V(0, -0.03 * math.sin(math.pi * u), z)
    tilt = Matrix.Rotation(math.radians(9) * math.sin(math.pi * u), 4, "Y")
    return Matrix.Translation(p) @ tilt @ lA.to_3x3().to_4x4()
for f in range(1, 380, 2):
    M = M_LIE2.inverted() @ head_world(f)
    l, q, _ = M.decompose(); head.rotation_mode = "QUATERNION"
    head.location = l; head.keyframe_insert("location", frame=f); head.rotation_quaternion = q; head.keyframe_insert("rotation_quaternion", frame=f)
def head_pt(f, model_pt):   # world position of a model-space point on the moving head
    return head_world(f) @ model_pt if f < 376 else M_root(f) @ model_pt
# collars: head collar visible with the head; body A collar always; body B collar under the seam once stitched
# marker line reveal (drawn 70-200)
for f, v in ((1, 0.08), (70, 0.08), (200, 0.62), (1770, 0.62)): node_key("M_MarkerLine", "Reveal", f, v)
hide_keys(D["MarkerLine"], [(1, False), (252, True)])
# stitches appear one by one 395-655 (6 already in on the far side)
st = sorted([o for o in D if o.name.startswith("Stitch_")], key=lambda o: o.name)
for i, s_ in enumerate(st):
    t_on = 1 if i < 6 else 395 + (i - 6) * 22
    hide_keys(s_, [(1, True), (max(2, t_on), False)])
hide_keys(D["Seam"], [(1, True), (392, False)])
hide_keys(D["Collar_Head"], [(1, False), (392, True)])
hide_keys(D["Collar_BodyB"], [(1, False), (392, True)])

# ------------------------------------------------------------------ eyes: closed (sedated) until beat 4, flicker, open, blinks; gaze; ears
LIDS = {s: (D["LidUp_" + s], D["LidLo_" + s]) for s in "LR"}
def lids(f, o):    # o: 0 closed .. 1 open
    for s in "LR":
        up, lo = LIDS[s]
        up.rotation_euler.x = math.radians(-3 - 72 * o); up.keyframe_insert("rotation_euler", frame=f, index=0)
        lo.rotation_euler.x = math.radians(3 + 60 * o); lo.keyframe_insert("rotation_euler", frame=f, index=0)
for f, o in ((1, 0.0), (700, 0.0), (706, 0.25), (712, 0.05), (724, 0.4), (730, 0.1), (745, 0.6), (765, 1.0), (812, 1.0), (816, 0.0), (822, 1.0),
             (858, 1.0), (862, 0.0), (868, 1.0), (960, 1.0), (964, 0.0), (970, 1.0),
             (1240, 1.0), (1244, 0.05), (1250, 1.0), (1330, 1.0), (1334, 0.05), (1340, 1.0),
             (1470, 1.0), (1560, 0.85), (1640, 0.55), (1700, 0.25), (1770, 0.2)):
    lids(f, o)
MH = "M_MonkeyHead"
for f, gx, gz in ((1, 0, 0), (765, 0.0, 0.0), (800, 0.0012, 0.0004), (850, -0.0008, 0.0), (889, 0.0014, 0.0006), (915, 0.0018, 0.0008),
                  (928, -0.0024, 0.0003), (950, -0.0022, 0.0), (980, 0.0006, 0.0012), (1027, 0.0, 0.0),
                  (1215, 0.0, 0.0), (1240, 0.0022, 0.0), (1265, -0.0022, 0.0), (1290, 0.0022, 0.0005), (1320, -0.0015, 0.0), (1350, 0.002, 0.0),
                  (1400, 0.0024, 0.0004), (1560, 0.0012, -0.0005), (1700, 0.0, -0.0008)):
    node_key(MH, "GazeX", f, gx); node_key(MH, "GazeZ", f, gz)
hk = head.data.shape_keys.key_blocks
for nm, keys in (("Ear_R", ((1, 0), (924, 0), (930, 1.0), (940, 0.7), (948, 1.0), (975, 0.2), (1000, 0))),
                 ("Ear_L", ((1, 0), (926, 0), (933, 0.8), (950, 0.4), (980, 0)))):
    for f, v in keys: hk[nm].value = v; hk[nm].keyframe_insert("value", frame=f)
# breathing (gentle chest swell on both bodies)
for bd in (D["MK_BodyA"], D["MK_BodyB"]):
    for f in range(1, 1771, 40):
        s = 1.0 + (0.012 if (f // 40) % 2 else 0.0)
        bd.scale = (s, 1.0, 1.0); bd.keyframe_insert("scale", frame=f)

# ------------------------------------------------------------------ surgical lamp swing (beat 1), nurse nudge (beat 3), dims (beat 9)
lp = D["Lamp_Pivot"]; lp.rotation_mode = "XYZ"
for f, a in ((1, 9.0), (30, -6.5), (60, 4.5), (92, -3.0), (125, 2.0), (160, -1.2), (200, 0.6), (240, 0.0), (470, 0.0), (490, 3.5), (520, -2.0), (560, 1.0), (600, 0.0)):
    lp.rotation_euler.y = math.radians(a); lp.keyframe_insert("rotation_euler", frame=f, index=1)
spot = D["Lamp_Spot"].data
for f, e in ((1, 0), (8, 900), (14, 300), (20, 950), (1560, 950), (1680, 120), (1770, 60)):
    spot.energy = e; spot.keyframe_insert("energy", frame=f)
lens_m = bpy.data.materials["M_LampLens"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f, e in ((1, 0), (8, 30), (14, 8), (20, 30), (1560, 30), (1680, 3), (1770, 1.5)):
    lens_m.default_value = e; lens_m.keyframe_insert("default_value", frame=f)
for i in range(6):
    bi = bpy.data.materials[f"M_Bulb_{i}"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    for f, e in ((1, 0), (8, 60), (14, 15), (20, 60), (1560, 60), (1680, 6), (1770, 3)):
        bi.default_value = e; bi.keyframe_insert("default_value", frame=f)
# exposure drop at the end + cyan window light breathing (days passing) + clock hands spin in beat 9
for f, e in ((1, 0.0), (1600, 0.0), (1770, -0.9)):
    sc.view_settings.exposure = e; sc.view_settings.keyframe_insert("exposure", frame=f)
cg = bpy.data.materials["M_CyanGlow"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f, e in ((1, 2.2), (1561, 2.2), (1600, 0.3), (1640, 2.4), (1680, 0.2), (1720, 2.2), (1770, 0.4)):
    cg.default_value = e; cg.keyframe_insert("default_value", frame=f)
for nm, turns in (("ClockHandMin", 36), ("ClockHandHour", 3)):
    h = D[nm]; h.rotation_mode = "XYZ"
    for f, r in ((1, 0.0), (1561, 0.25), (1770, 0.25 + turns)):
        h.rotation_euler.y = 2 * math.pi * r * (1 if nm.endswith("Min") else 1); h.keyframe_insert("rotation_euler", frame=f, index=1)

# ------------------------------------------------------------------ ECG trace on the monitor (procedural), beeping lamp
mon = D["Monitor"]
SCR = V(3.05, 0.582, 1.075); SCR_R = 0.075
bpy.ops.mesh.primitive_circle_add(vertices=48, radius=SCR_R, fill_type="NGON", location=SCR, rotation=(math.radians(90), 0, 0))
ecg = bpy.context.active_object; ecg.name = "ECG_Trace"
em = bpy.data.materials.new("M_ECG"); em.use_nodes = True; nt = em.node_tree
for n_ in list(nt.nodes):
    if n_.type != "OUTPUT_MATERIAL": nt.nodes.remove(n_)
N = nt.nodes.new; Lk = nt.links.new
tc = N("ShaderNodeTexCoord"); sp = N("ShaderNodeSeparateXYZ"); Lk(tc.outputs["Object"], sp.inputs[0])
T = N("ShaderNodeValue"); T.name = T.label = "ECGTime"
A = N("ShaderNodeValue"); A.name = A.label = "ECGAmp"
def math_(op, a, b=None, c=None):
    m = N("ShaderNodeMath"); m.operation = op
    for i, x in enumerate((a, b, c)):
        if x is None: continue
        if isinstance(x, (int, float)): m.inputs[i].default_value = x
        else: Lk(x, m.inputs[i])
    return m.outputs[0]
xs = math_("MULTIPLY", sp.outputs["X"], 1.0 / (2 * SCR_R))           # -0.5..0.5 across the screen
u = math_("FRACT", math_("SUBTRACT", math_("MULTIPLY", xs, 1.6), T.outputs[0]))
def bump(c, w, h):
    d = math_("MULTIPLY", math_("SUBTRACT", u, c), w)
    return math_("MULTIPLY", math_("EXPONENT", math_("MULTIPLY", math_("MULTIPLY", d, d), -1.0)), h)
wave = math_("ADD", math_("ADD", bump(0.5, 60, 1.0), bump(0.56, 45, -0.35)), math_("ADD", bump(0.3, 18, 0.12), bump(0.75, 14, 0.22)))
wave = math_("MULTIPLY", math_("MULTIPLY", wave, A.outputs[0]), SCR_R * 0.62)
dist = math_("ABSOLUTE", math_("SUBTRACT", sp.outputs["Z"] if False else sp.outputs["Y"], wave))
line = math_("SUBTRACT", 1.0, math_("MINIMUM", math_("DIVIDE", dist, 0.0028), 1.0))
# phosphor: brighter near the sweep head (u near the leading edge)
sweep = math_("FRACT", math_("SUBTRACT", math_("MULTIPLY", xs, 1.0), math_("MULTIPLY", T.outputs[0], 0.625)))
glowk = math_("ADD", 0.35, math_("MULTIPLY", math_("POWER", sweep, 3.0), 1.2))
inten = math_("MULTIPLY", math_("MULTIPLY", line, glowk), 14.0)
grid = math_("MULTIPLY", math_("ADD", math_("LESS_THAN", math_("ABSOLUTE", math_("SINE", math_("MULTIPLY", sp.outputs["X"], 250.0))), 0.04),
                               math_("LESS_THAN", math_("ABSOLUTE", math_("SINE", math_("MULTIPLY", sp.outputs["Y"], 250.0))), 0.04)), 0.25)
e = N("ShaderNodeEmission"); e.inputs["Color"].default_value = (0.25, 1.0, 0.35, 1)
Lk(math_("ADD", math_("ADD", inten, grid), 0.15), e.inputs["Strength"])
Lk(e.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
ecg.data.materials.append(em); ecg.parent = None
# time: steady rhythm then slowing, amplitude to flat
tval = 0.0; prev = 1
rate = lambda f: 1.15 if f < 1561 else max(0.0, 1.15 * (1 - (f - 1561) / 150.0))
for f in range(1, 1771, 4):
    tval += rate(f) * 4 / FPS
    T.outputs[0].default_value = tval; T.outputs[0].keyframe_insert("default_value", frame=f)
for f, a in ((1, 1.0), (1561, 1.0), (1650, 0.45), (1720, 0.0), (1770, 0.0)):
    A.outputs[0].default_value = a; A.outputs[0].keyframe_insert("default_value", frame=f)
for o in ("ECG_Trace",):
    pass
for nm_, loc_, sz_ in (("Scope_LabelPlate", V(3.05, 0.580, 1.168), (0.285, 0.006, 0.045)),):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc_); pl_ = bpy.context.active_object; pl_.name = nm_; pl_.scale = sz_
    pm_ = bpy.data.materials.new("M_ScopePlate"); pm_.use_nodes = True; pm_.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.03, 0.03, 0.035, 1)
    pm_.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.5; pl_.data.materials.append(pm_)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.008, location=SCR + V(0.1, -0.005, -0.1))
bl = bpy.context.active_object; bl.name = "Beep_Lamp"; blm = bpy.data.materials.new("M_BeepLamp"); blm.use_nodes = True
bp = blm.node_tree.nodes["Principled BSDF"]; bp.inputs["Base Color"].default_value = (0.3, 0.02, 0.02, 1); bp.inputs["Emission Color"].default_value = (1, 0.1, 0.05, 1)
bl.data.materials.append(blm)
tt = 0.0; f = 1
beat_frames = []
while f < 1720:
    beat_frames.append(f); f += int(round(FPS / 1.15 * (1 if f < 1561 else 1 + (f - 1561) / 60.0)))
for bf in beat_frames:
    for df, e_ in ((0, 0.0), (1, 25.0), (7, 0.0)):
        bp.inputs["Emission Strength"].default_value = e_; bp.inputs["Emission Strength"].keyframe_insert("default_value", frame=bf + df)
# the T2 / Corner fades + void
for m in all_mats_with("Fade_T2"):
    for f, v in ((1, 1.0), (1022, 1.0), (1034, 0.0), (1770, 0.0)): node_key(m, "Fade_T2", f, v)
for m in all_mats_with("Fade_Corner"):
    for f, v in ((1, 1.0), (1016, 1.0), (1018, 0.0), (1188, 0.0), (1212, 1.0)): node_key(m, "Fade_Corner", f, v)
for f, v in ((1, 0.0), (1020, 0.0), (1034, 1.0), (1188, 1.0), (1210, 0.0)): node_key("M_XR_Void", "VoidOn", f, v)
for m in all_mats_with("XRay"):
    for f, v in ((1, 0.0), (1030, 0.0), (1046, 1.0), (1185, 1.0), (1205, 0.0)): node_key(m, "XRay", f, v)
for o in D:
    if o.get("xray"): hide_keys(o, [(1, True), (1030, False), (1206, True)])
# pulse runs from the brain down the head cord and stops at the gap (twice)
pulse = D["XR_Pulse"]; bb = D["XR_Brain"].location + V(0, 0, -0.022) + V(-0.385, -0.923, 0).normalized() * 0.005
gap = NC + V(0, 0, 0.022)
for f0 in (1050, 1110):
    for df, u_ in ((0, 0.0), (28, 1.0), (40, 1.0)):
        pulse.location = bb.lerp(gap, u_); pulse.keyframe_insert("location", frame=f0 + df)
# everything else hides while the void is fully opaque
KEEP = {"MK_Head", "MK_BodyB", "XR_Void", "CAM_Film", "MonkeyRootB"}
for o in D:
    if o.name in KEEP or o.get("xray") or o.type in ("CAMERA",): continue
    if o.parent and o.parent.name in ("MK_Head", "MK_BodyB") and o.type != "EMPTY": continue
    if o.name.startswith(("EyePivot", "LidUp", "LidLo", "Seam", "Stitch_", "Collar_BodyB", "Collar_Head")): continue
    if o.type in ("MESH", "CURVE", "LIGHT"):
        hide_keys(o, [(1, o.hide_render), (1036, True), (1187, False if not o.hide_render else True)])

# ------------------------------------------------------------------ people
SURG = Human(make_human_ctrl(D["Surgeon"])); NURSE = Human(make_human_ctrl(D["Nurse"]))
def yaw_to(p, q): v = q - p; return math.degrees(math.atan2(v.x, -v.y))
def pose(H, f, pos, yaw, flex=0.0, twist=0.0, side=0.0, headr=(0.0, 0.0), crouch=0.0, feet=None):
    H.key_root(f, V(pos.x, pos.y, H.root_head.z - crouch), yaw=yaw, flex=flex * 0.4, side=side)
    H.key_spine(f, flex=flex, twist=twist, side=side, head=headr)
    if feet is None:
        for s in "LR": H.key_foot(s, f, H.foot_xy(s, V(pos.x, pos.y, 0), yaw), yaw)
    else:
        for s, (xy, yw) in feet.items(): H.key_foot(s, f, xy, yw)
def hand(H, s, f, W, d, n, elbow_out=0.35, yaw=0.0):
    sx = 1 if s == "L" else -1
    side = Matrix.Rotation(math.radians(yaw), 3, "Z") @ V(sx, 0, 0)
    H.key_hand(s, f, W, d.normalized(), n.normalized(), pole=W + side * elbow_out + V(0, 0, -0.25))
def hang(H, s, f, pos, yaw, fwd=0.0):
    sx = 1 if s == "L" else -1
    Rz = Matrix.Rotation(math.radians(yaw), 3, "Z")
    W = V(pos.x, pos.y, 0) + Rz @ V(sx * 0.22, -fwd, 0) + V(0, 0, H.root_head.z * 0.87)
    hand(H, s, f, W, V(0, 0, -1) + Rz @ V(0, -0.15, 0), Rz @ V(-sx, 0, 0), 0.3, yaw)

# Surgeon: S0 in front of table 1 / S1 in front of table 2
S0 = V(-0.28, -0.6, 0); S1 = V(0.45, -0.62, 0)
Y0 = 180.0 + 8; Y1 = 180.0 - 12
pen = D["MarkerPen"]; nh = D["NeedleHolder"]; fcp = D["Forceps"]
srig = D["Surgeon"]
def neck_ring(center_M, a, r=0.075):
    return center_M @ (NC + V(r * math.cos(a), 0.85 * r * math.sin(a), 0.0))
# beat 1: marker drawing 40-200, left hand steadies the head
for f in range(1, 252, 6):
    sw = 0.5 + 0.5 * math.sin(f / 24.0)
    pose(SURG, f, S0, Y0, flex=26 + 3 * sw, twist=-6, headr=(18, 4))
    a = -1.0 + 2.6 * smooth((f - 60) / 140.0)
    tip = neck_ring(M_LIE1, a, 0.081) if f > 40 else neck_ring(M_LIE1, -1.0, 0.11) + V(0, -0.05, 0.08)
    if f > 205: tip = neck_ring(M_LIE1, 1.6, 0.11) + V(0.0, -0.08, 0.10 * smooth((f - 205) / 20))
    hand(SURG, "R", f, tip + V(0, -0.03, 0.10), V(0.1, 0.3, -1), V(1, 0, 0.2), 0.35, Y0)
    hand(SURG, "L", f, head_pt(f, EYEMID + V(0.05, 0.03, 0.05)) + V(0, 0, 0.04), V(0.3, 1, -0.6), V(0, 0, -1), 0.4, Y0)
# pen: in the right hand until put down on the drape at ~232
def wrist_M(f, s):
    ev(f); pb = SURG.r.PB["wrist." + s]
    return srig.matrix_world @ pb.matrix
for f in range(1, 240, 3):
    M = wrist_M(f, "R")
    p = M @ V(0, 0.09, 0.02)
    pen.location = p; pen.keyframe_insert("location", frame=f)
    pen.rotation_mode = "QUATERNION"; pen.rotation_quaternion = (M.to_quaternion() @ Quaternion((1, 0, 0), math.radians(90))); pen.keyframe_insert("rotation_quaternion", frame=f)
pen.location = V(-0.2, -0.16, 0.925); pen.keyframe_insert("location", frame=246)
pen.rotation_quaternion = Quaternion((0, 1, 0), math.radians(90)) @ Quaternion((0, 0, 1), math.radians(20)); pen.keyframe_insert("rotation_quaternion", frame=246)
# beat 2: both hands cup the head (under jaw / behind skull), lift, side-step, place on body B
GRIP_L = EYEMID + V(0.04, 0.06, -0.075)    # model-space points on the head: under the jaw, behind the skull
GRIP_R = EYEMID + V(-0.02, 0.10, 0.07)
for f in list(range(214, 400, 3)) + [400]:
    u = smooth((f - 290) / 60.0)
    pos = S0.lerp(S1, u); yw = Y0 + (Y1 - Y0) * u
    feet = {"L": (SURG.foot_xy("L", S0.lerp(S1, smooth((f - 290) / 30.0)), yw), yw), "R": (SURG.foot_xy("R", S0.lerp(S1, smooth((f - 318) / 30.0)), yw), yw)}
    lift = {s: 0.0 for s in "LR"}
    pose(SURG, f, pos + V(0, 0, 0), yw, flex=30 - 8 * math.sin(math.pi * smooth((f - 262) / 110)), twist=-4, headr=(20, 0), feet=feet)
    for s, (xy, yw_) in feet.items():
        ph0 = 290 if s == "L" else 318
        lf = 0.07 * math.sin(math.pi * max(0.0, min(1.0, (f - ph0) / 30.0)))
        SURG.key_foot(s, f, xy, yw_, lift=lf)
    if f <= 384:
        hand(SURG, "L", f, head_pt(f, GRIP_L) + V(0, 0, -0.012), V(0.6, 0.4, -0.3), V(0, 0, 1), 0.4, yw)
        hand(SURG, "R", f, head_pt(f, GRIP_R) + V(0, 0, 0.01), V(-0.6, 0.5, -0.4), V(0.3, 0, -1), 0.4, yw)
    else:
        k = smooth((f - 384) / 16.0)
        hand(SURG, "L", f, head_pt(384, GRIP_L) + V(-0.05, -0.12, 0.08) * k, V(0.6, 0.4, -0.3), V(0, 0, 1), 0.4, yw)
        hand(SURG, "R", f, head_pt(384, GRIP_R) + V(0.03, -0.10, 0.10) * k, V(-0.6, 0.5, -0.4), V(0.3, 0, -1), 0.4, yw)
# beat 3: stitching 400-665 - right hand needle holder arcs in at each stitch, left hand forceps holds the edge
stitch_ang = [2 * math.pi * i / len(st) for i in range(len(st))]
for f in list(range(403, 672, 3)):
    pose(SURG, f, S1, Y1, flex=34, twist=-3, headr=(24, -4))
    k = (f - 395) // 22 + 6; ph = ((f - 395) % 22) / 22.0
    a = stitch_ang[min(k, len(st) - 1)] + 0.25
    seam_pt = neck_ring(M_LIE2, a, 0.074)
    arc = V(0.0, -0.03 * math.cos(2 * math.pi * ph), 0.03 * math.sin(2 * math.pi * ph))
    hand(SURG, "R", f, seam_pt + V(0.03, -0.11, 0.09) + arc, V(0.2, 0.6, -0.6), V(1, 0, 0.4), 0.35, Y1)
    hand(SURG, "L", f, neck_ring(M_LIE2, a - 0.6, 0.08) + V(-0.06, -0.09, 0.09), V(-0.1, 0.6, -0.6), V(-1, 0, 0.3), 0.35, Y1)
# beats 4-5: steps back, watches; snaps fingers near the ear at 920 (the "hear" cue together with the bowl)
S2 = V(0.25, -0.95, 0)
for f in list(range(672, 1040, 6)):
    u = smooth((f - 672) / 40.0)
    pos = S1.lerp(S2, u)
    pose(SURG, f, pos, Y1 - 10 * u, flex=18 - 8 * u, twist=6 * u, headr=(18, -6 + 12 * math.sin(f / 50.0)))
    if 890 < f < 960:
        k = smooth((f - 890) / 20.0) * (1 - smooth((f - 945) / 15.0))
        hang(SURG, "L", f, pos, Y1)
        hand(SURG, "R", f, V(0.48, -0.42, 1.25).lerp(V(0.3, -0.75, 1.0), 1 - k), V(0.3, 1, 0.5), V(1, 0, 0), 0.3, Y1)
    else:
        for s in "LR": hand(SURG, s, f, pos + Matrix.Rotation(math.radians(Y1), 3, "Z") @ V((0.08 if s == "L" else -0.08), -0.28, 0) + V(0, 0, 1.0), V(0, 1, 0.2) if False else Matrix.Rotation(math.radians(Y1), 3, "Z") @ V((-1 if s == "L" else 1), -0.3, 0), V(0, 0, 1), 0.3, Y1)
# beats 7-9: recovery corner. Surgeon beside the chair waves a hand in front of the monkey (no reaction), then clipboard at the monitor
S3 = V(1.86, 1.0, 0); Y3 = yaw_to(S3, CH + V(0, 0.2, 0))
S4 = V(2.52, 0.38, 0); Y4 = yaw_to(S4, V(3.05, 0.95, 0))
board = D["Forceps"]
for f in list(range(1190, 1771, 6)):
    if f < 1380:
        pose(SURG, f, S3, Y3, flex=22, twist=-5, headr=(22, 0), crouch=0.05)
        face_w = M_CHAIR @ EYEMID
        wv = math.sin((f - 1230) / 7.0) if 1225 < f < 1310 else 0.0
        Rz = Matrix.Rotation(math.radians(Y3), 3, "Z")
        hand(SURG, "R", f, face_w + (S3 - face_w).normalized() * 0.16 + V(0, 0, 0.05) + Rz @ V(0.06 * wv, 0, 0), V(0, 0, 1), Rz @ V(0, 1, 0), 0.35, Y3)
        hang(SURG, "L", f, S3, Y3, 0.05)
    else:
        u = smooth((f - 1380) / 40.0)
        pos = S3.lerp(S4, u); yw = Y3 + (Y4 - Y3) * u
        pose(SURG, f, pos, yw, flex=12 + 10 * smooth((f - 1600) / 80.0), headr=(18 + 14 * smooth((f - 1600) / 80.0), 0))
        Rz = Matrix.Rotation(math.radians(yw), 3, "Z")
        cb = pos + Rz @ V(0.05, -0.32, 0) + V(0, 0, 1.08)
        hand(SURG, "L", f, cb + Rz @ V(0.1, 0.02, 0), Rz @ V(-1, 0, 0), V(0, 0, 1), 0.3, yw)
        wr = math.sin(f / 3.0) * 0.01 if 1400 < f < 1560 else 0.0
        hand(SURG, "R", f, cb + Rz @ V(-0.03 + wr, -0.02, 0.04), Rz @ V(0.3, -1, -0.5), V(0, 0, 1), 0.35, yw)
hide_keys_people = []
for ob in [D["Surgeon"]] + [c for c in D["Surgeon"].children]:
    hide_keys(ob, [(1, False), (1036, True), (1187, False)])
# Nurse: wheels the trolley in (beat 1), holds the bowl, drops it (beat 5), at the monitor with notes (7-9)
tro = [o for o in D if o.name in ("Trolley", "Tray", "Instruments", "Bowl")]
TRO_END = D["Trolley"].location.copy()
for o in tro:
    base = o.location.copy()
    for f, u in ((1, 0.0), (150, 1.0)):
        o.location = base + V(-0.55, -0.75, 0) * (1 - u); o.keyframe_insert("location", frame=f)
NP0 = TRO_END + V(-0.55, -0.75, 0) + V(-0.15, -0.55, 0); NP1 = TRO_END + V(-0.12, -0.55, 0)
ny = yaw_to(NP1, TRO_END)
NURSE.walk(lambda f: NP0.lerp(NP1, smooth((f - 1) / 150.0)).to_3d(), lambda f: ny, 1, 160, stride=0.55, duty=0.6, lift=0.07, bob=0.018, crouch=0.04, lean=8)
for f in range(1, 162, 4):
    p = NP0.lerp(NP1, smooth((f - 1) / 150.0))
    for s in "LR":
        Rz = Matrix.Rotation(math.radians(ny), 3, "Z")
        hand(NURSE, s, f, p + Rz @ V((0.16 if s == "L" else -0.16), -0.38, 0) + V(0, 0, 0.88), Rz @ V(0, -1, -0.3), V(0, 0, 1), 0.3, ny)
NP2 = V(-0.85, -0.62, 0); ny2 = yaw_to(NP2, V(0.0, 0.05, 0))
bowl = D["Bowl"]
for f in list(range(166, 1040, 6)):
    u = smooth((f - 166) / 40.0)
    p = NP1.lerp(NP2, u); yw = ny + (ny2 - ny) * u
    pose(NURSE, f, p, yw, flex=10, headr=(12, 10 * math.sin(f / 60.0)))
    Rz = Matrix.Rotation(math.radians(yw), 3, "Z")
    if 470 < f < 530:   # reaches up to nudge the lamp handle
        k = math.sin(math.pi * (f - 470) / 60.0)
        hand(NURSE, "R", f, (p + V(0, 0, 1.1) + Rz @ V(-0.15, -0.3, 0)).lerp(V(0.0, 0.15, 1.82), k), V(0, 0, 1), Rz @ V(0, -1, 0), 0.3, yw)
    else:
        hang(NURSE, "R", f, p, yw, 0.05)
    hand(NURSE, "L", f, p + Rz @ V(0.12, -0.3, 0) + V(0, 0, 0.95), Rz @ V(-1, -0.4, 0), V(0, 0, 1), 0.3, yw)
# bowl: on the tray -> in the nurse's left hand (from 200) -> slips at 918, hits the floor 940, bounces, rattles
for f in range(1, 918, 6):
    if f < 200: continue
    ev(f); M = D["Nurse"].matrix_world @ NURSE.r.PB["wrist.L"].matrix
    bowl.location = M @ V(0, 0.08, 0.04); bowl.keyframe_insert("location", frame=f)
p0 = bowl.location.copy()
for df, dz, dx in ((0, 0, 0), (10, -0.35, 0.05), (22, -(p0.z - 0.02), 0.1), (28, -(p0.z - 0.02) + 0.09, 0.14), (34, -(p0.z - 0.02), 0.17), (38, -(p0.z - 0.02) + 0.03, 0.18), (42, -(p0.z - 0.02), 0.19)):
    bowl.location = p0 + V(dx, -dx * 0.5, dz); bowl.keyframe_insert("location", frame=918 + df)
bowl.rotation_mode = "XYZ"
for df, rx in ((0, 0), (22, 70), (28, 140), (34, 175), (42, 180)):
    bowl.rotation_euler.x = math.radians(rx); bowl.keyframe_insert("rotation_euler", frame=918 + df, index=0)
# nurse at the monitor (beats 7-9)
NP3 = V(3.45, 0.45, 0); ny3 = yaw_to(NP3, V(3.05, 0.95, 0))
for f in list(range(1190, 1771, 6)):
    pose(NURSE, f, NP3, ny3, flex=14, headr=(16 + 10 * smooth((f - 1620) / 60.0), 6 * math.sin(f / 40.0)))
    Rz = Matrix.Rotation(math.radians(ny3), 3, "Z")
    if 1330 < f < 1400:
        k = math.sin(math.pi * (f - 1330) / 70.0)
        hand(NURSE, "R", f, (NP3 + Rz @ V(-0.15, -0.3, 0) + V(0, 0, 0.9)).lerp(V(3.13, 0.6, 1.0), k), Rz @ V(0, -1, 0), V(0, 0, 1), 0.3, ny3)
    else:
        hang(NURSE, "R", f, NP3, ny3, 0.08)
    hang(NURSE, "L", f, NP3, ny3, 0.08)
for ob in [D["Nurse"]] + [c for c in D["Nurse"].children]:
    hide_keys(ob, [(1, False), (1036, True), (1187, False)])
# needle holder / forceps follow the surgeon's hands (beat 3 only), parked on the tray otherwise
for tool, s, off in ((nh, "R", V(0, 0.07, 0.0)), (fcp, "L", V(0, 0.07, 0.0))):
    tool.rotation_mode = "QUATERNION"
    for f in list(range(380, 680, 3)):
        M = wrist_M(f, s)
        tool.location = M @ off; tool.keyframe_insert("location", frame=f)
        tool.rotation_quaternion = M.to_quaternion() @ Quaternion((1, 0, 0), math.radians(90)); tool.keyframe_insert("rotation_quaternion", frame=f)
    hide_keys(tool, [(1, True), (382, False), (676, True)])

# ------------------------------------------------------------------ camera: one spline (keys in world, or in monkey-B space during the void)
cam_d = bpy.data.cameras.new("CAM_Film"); cam_d.lens = 28; cam_d.sensor_fit = "AUTO"; cam_d.clip_start = 0.01
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 2.8
cam = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(cam); sc.camera = cam
void = D["XR_Void"]; void.parent = cam; void.matrix_parent_inverse = Matrix.Identity(4); void.location = (0, 0, 0)
kl = bpy.data.lights.new("XR_Key", "AREA"); kl.energy = 0; kl.size = 0.4; kl.color = (0.85, 1.0, 0.95)
klo = bpy.data.objects.new("XR_Key", kl); sc.collection.objects.link(klo); klo.parent = cam; klo.location = (0.25, 0.3, 0.1)
for f, e in ((1, 0), (1028, 0), (1036, 6), (1188, 6), (1206, 0)): kl.energy = e; kl.keyframe_insert("energy", frame=f)
NBp = NB; FBp = FB
L = lambda f: M_root(f)
FWW = M_LIE2.to_3x3() @ V(-0.385, -0.923, 0)       # monkey B face direction in the world while lying
UPW = V(0, 0, 1)
# (frame, pos, aim, lens, up, space)   space 'W' world, 'B' monkey-B model space
K = [
 (1,    V(0.95, -1.65, 0.48), V(-0.35, 0.1, 0.95), 22, UPW, "W"),
 (61,   V(0.6, -0.95, 1.15), NA + V(0, 0.05, 0), 28, UPW, "W"),
 (121,  V(0.18, -0.38, 1.32), NA, 38, UPW, "W"),
 (181,  NA + V(0.26, -0.04, 0.17), NA, 50, UPW, "W"),
 (241,  V(0.16, -0.42, 1.52), V(-0.12, -0.05, 1.02), 30, UPW, "W"),
 (290,  V(0.0, -0.78, 1.78), V(0.05, -0.05, 1.08), 26, UPW, "W"),
 (330,  V(0.2, -0.42, 1.82), V(0.2, -0.02, 1.04), 22, V(0, 1, 0.3), "W"),
 (365,  V(0.9, -0.55, 1.5), NBp, 30, UPW, "W"),
 (420,  NBp + V(0.24, -0.14, 0.2), NBp, 45, UPW, "W"),
 (480,  NBp + V(0.27, -0.08, 0.11), NBp, 55, UPW, "W"),
 (540,  NBp + V(0.22, 0.10, 0.20), NBp, 55, UPW, "W"),
 (600,  NBp + V(0.27, 0.03, 0.03), NBp + V(0, 0, 0.04), 45, UPW, "W"),
 (650,  NBp + V(0.24, -0.12, 0.06), NBp + V(0.02, -0.02, 0.0), 45, UPW, "W"),
 (700,  FBp + FWW * 0.32 + V(0, -0.18, 0.08), FBp, 40, UPW, "W"),
 (760,  FBp + FWW * 0.24 + V(0, -0.08, 0.05), FBp, 52, UPW, "W"),
 (820,  FBp + FWW * 0.13 + V(0, -0.02, 0.02), FBp, 70, UPW, "W"),
 (880,  FBp + FWW * 0.18 + V(0, 0.06, 0.06), FBp, 55, UPW, "W"),
 (930,  FBp + FWW * 0.16 + V(0, 0.16, 0.12), FBp, 45, UPW, "W"),
 (975,  FBp + V(0.06, 0.14, 0.25), FBp + V(-0.02, 0.05, 0), 38, V(0, -1, 0.4), "W"),
 (1005, NBp + V(0.0, 0.02, 0.33), NBp + V(0, 0.03, 0), 34, V(0, -1, 0), "W"),
 (1030, NBp + V(0.0, 0.03, 0.22), NBp + V(0, 0.03, 0), 34, V(0, -1, 0), "W"),
 (1064, NC + V(0.24, 0.02, 0.0), NC + V(0, 0.02, -0.02), 34, V(0, 0, 1), "B"),
 (1110, V(0.30, -0.02, 0.26), V(0.0, -0.22, 0.25), 28, V(0, 0, 1), "B"),
 (1160, V(0.16, -0.40, 0.62), EYEMID + V(-0.02, 0.04, 0.0), 30, V(0, 0, 1), "B"),
 (1190, V(-0.05, -0.80, 0.46), V(-0.05, -0.32, 0.32), 30, V(0, 0, 1), "B"),
 (1250, CH + V(-0.6, -1.35, 0.62), CH + V(0, 0.25, 0.62), 24, UPW, "W"),
 (1320, CH + V(0.35, -1.45, 0.85), CH + V(0.05, 0.2, 0.66), 26, UPW, "W"),
 (1380, V(2.85, -0.42, 1.08), V(2.95, 0.7, 0.95), 30, UPW, "W"),
 (1440, SCR + V(-0.06, -0.42, 0.05), SCR, 45, UPW, "W"),
 (1500, SCR + V(0.04, -0.24, 0.02), SCR, 50, UPW, "W"),
 (1560, SCR + V(0.24, -0.30, 0.09), SCR + V(-0.02, 0, 0), 40, UPW, "W"),
 (1620, V(3.45, -0.5, 1.4), V(2.5, 0.9, 0.75), 30, UPW, "W"),
 (1700, V(1.6, -2.3, 1.85), V(1.6, 0.8, 0.8), 24, UPW, "W"),
 (1770, V(1.2, -2.85, 2.05), V(1.4, 0.7, 0.85), 24, UPW, "W"),
]
# convert every key to monkey-B space with the root at that frame, spline there, map back per frame
def to_local(f, p, space):
    return p if space == "B" else M_root(f).inverted() @ p
def dir_local(f, d, space):
    return d if space == "B" else M_root(f).to_3x3().inverted() @ d
fp = catmull([(k[0], to_local(k[0], k[1], k[5])) for k in K])
fa = catmull([(k[0], to_local(k[0], k[2], k[5])) for k in K])
fl = catmull([(k[0], float(k[3])) for k in K])
fup = catmull([(k[0], dir_local(k[0], k[4], k[5]).normalized()) for k in K])
cam.rotation_mode = "QUATERNION"; prevq = None
CAMLOG = []
for f in range(1, 1771):
    M = M_root(f)
    p = M @ fp(f); a = M @ fa(f); up = (M.to_3x3() @ fup(f)).normalized()
    fwd = (a - p).normalized(); rgt = fwd.cross(up).normalized(); upv = rgt.cross(fwd)
    q = Matrix((rgt, upv, -fwd)).transposed().to_quaternion()
    if prevq is not None and prevq.dot(q) < 0: q = -q
    prevq = q
    cam.location = p; cam.keyframe_insert("location", frame=f)
    cam.rotation_quaternion = q; cam.keyframe_insert("rotation_quaternion", frame=f)
    cam_d.lens = fl(f); cam_d.keyframe_insert("lens", frame=f)
    cam_d.dof.focus_distance = (a - p).length; cam_d.dof.keyframe_insert("focus_distance", frame=f)
    CAMLOG.append((f, tuple(round(x, 3) for x in p), tuple(round(x, 3) for x in a), round(fl(f), 1)))
json.dump(CAMLOG[::30], open(os.path.join(HERE, "..", "camera_path.json"), "w"))
for o in D: set_const(o)
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ANIM_SAVED", OUT)
