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
NRM = nref.matrix_world.copy()
def neck_ring(center_M, a, r=0.075):
    return center_M @ (NRM @ V(r * math.cos(a), 0.85 * r * math.sin(a), 0.0))
A_UP = max([i * 2 * math.pi / 72 - math.pi for i in range(72)], key=lambda a: (M_LIE1 @ (NRM @ V(math.cos(a), 0.85 * math.sin(a), 0))).z)
print("A_UP", A_UP)
def rev_of(a): return ((a + math.pi) % (2 * math.pi)) / (2 * math.pi)
CH = D["Chair"].location.copy()
SEAT = 0.409
M_CHAIR = Matrix.Translation(CH + V(0.0, 0.26, SEAT + 0.022)) @ Matrix.Rotation(math.radians(-7), 4, "X") @ Matrix.Rotation(math.radians(5), 4, "Y")
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
A0, A1 = A_UP - 1.3, A_UP + 1.3
bpy.data.materials["M_MarkerLine"].node_tree.nodes["RevealStart"].outputs[0].default_value = A0 + math.pi
for f in range(1, 1771, 10):
    a_ = A0 + (A1 - A0) * smooth((f - 60) / 140.0)
    node_key("M_MarkerLine", "Reveal", f, max(0.0, min(1.0, (a_ - A0) / (2 * math.pi) + 0.0)))
hide_keys(D["MarkerLine"], [(1, False), (252, True)])
# stitches appear one by one 395-655 (6 already in on the far side)
st = sorted([o for o in D if o.name.startswith("Stitch_")], key=lambda o: o.name)
_sa = [2 * math.pi * i / len(st) for i in range(len(st))]
_up = sorted([i for i in range(len(st)) if (M_LIE2 @ (NRM @ V(math.cos(_sa[i]), 0.85 * math.sin(_sa[i]), 0))).z >= (M_LIE2 @ NRM.translation).z - 0.01],
             key=lambda i: ((_sa[i] - A_UP + math.pi) % (2 * math.pi)))
STITCH_ORDER = _up
for i, s_ in enumerate(st):
    t_on = 1 if i not in _up else 395 + _up.index(i) * 26
    hide_keys(s_, [(1, True), (max(2, t_on), False)])
print("STITCH up", len(_up))
hide_keys(D["Seam"], [(1, True), (392, False)])
hide_keys(D["Collar_Head"], [(1, True), (256, False), (392, True)])
hide_keys(D["Collar_BodyA"], [(1, True), (256, False)])
hide_keys(D["Collar_BodyB"], [(1, False), (392, True)])

# ------------------------------------------------------------------ eyes: closed (sedated) until beat 4, flicker, open, blinks; gaze; ears
LIDS = {s: (D["LidUp_" + s], D["LidLo_" + s]) for s in "LR"}
def lids(f, o):    # o: 0 closed .. 1 open
    for s in "LR":
        up, lo = LIDS[s]
        up.rotation_euler.x = math.radians(4.0 - 79 * o); up.keyframe_insert("rotation_euler", frame=f, index=0)
        lo.rotation_euler.x = math.radians(1.0 + 40 * o); lo.keyframe_insert("rotation_euler", frame=f, index=0)
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
hk["Ears_Round"].value = 0.75; hk["Ears_Round"].keyframe_insert("value", frame=1)
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
for f, e in ((1, 0), (8, 650), (14, 220), (20, 650), (1560, 650), (1680, 90), (1770, 45)):
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
    if o.parent and o.parent.name in ("MK_Head", "MK_BodyB") and o.type != "EMPTY" and not o.name.startswith(("Stitch_", "Seam", "Collar_")): continue
    if o.name.startswith(("EyePivot", "LidUp", "LidLo")): continue
    if o.type in ("MESH", "CURVE", "LIGHT"):
        fc_ = None
        if o.animation_data and o.animation_data.action:
            for layer in getattr(o.animation_data.action, "layers", []):
                for strip in layer.strips:
                    for cb in strip.channelbags:
                        for fc in cb.fcurves:
                            if fc.data_path == "hide_render": fc_ = fc
        if fc_ is not None:
            v1187 = bool(fc_.evaluate(1187) > 0.5)
            hide_keys(o, [(1036, True), (1187, v1187)])
        else:
            hide_keys(o, [(1, o.hide_render), (1036, True), (1187, False if not o.hide_render else True)])

# ------------------------------------------------------------------ people
SURG = Human(make_human_ctrl(D["Surgeon"])); NURSE = Human(make_human_ctrl(D["Nurse"]))
def yaw_to(p, q): v = q - p; return math.degrees(math.atan2(v.x, -v.y))
def pose(H, f, pos, yaw, flex=0.0, twist=0.0, side=0.0, headr=(0.0, 0.0), crouch=0.0, feet=None, step=None):
    H.key_root(f, V(pos.x, pos.y, H.root_head.z - crouch), yaw=yaw, flex=flex * 0.4, side=side)
    H.key_spine(f, flex=flex, twist=twist, side=side, head=headr)
    if step is not None:   # (p0, y0, p1, y1, u): left foot steps in the first half, right foot in the second
        p0, y0, p1, y1, u = step
        for s, k in (("L", max(0.0, min(1.0, 2 * u))), ("R", max(0.0, min(1.0, 2 * u - 1)))):
            kk = smooth(k); yw = y0 + (y1 - y0) * kk
            xy = H.foot_xy(s, V(p0.x, p0.y, 0).lerp(V(p1.x, p1.y, 0), kk), yw)
            H.key_foot(s, f, xy, yw, lift=0.06 * math.sin(math.pi * k), pitch=12 * math.sin(math.pi * k))
    elif feet is None:
        for s in "LR": H.key_foot(s, f, H.foot_xy(s, V(pos.x, pos.y, 0), yaw), yaw)
    else:
        for s, (xy, yw) in feet.items(): H.key_foot(s, f, xy, yw)
CURL_SIGN = float(os.environ.get("CURL_SIGN", "1"))
def curl(H, s, f, k, base=8.0):
    for fi in range(1, 6):
        for seg, w in ((1, 0.6), (2, 1.0), (3, 0.8)):
            n = f"finger{fi}-{seg}.{s}"
            if n not in H.r.PB or (fi == 1 and seg == 1): continue
            pb = H.r.PB[n]; pb.rotation_mode = "QUATERNION"
            sg = 1.0 if s == "L" else -1.0
            ang = math.radians(sg * (base + (38 if s == "L" else 55) * k) * w * (0.5 if fi == 1 else 1.0))
            pb.rotation_quaternion = Quaternion((1, 0, 0), ang); pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
def hand(H, s, f, W, d, n, elbow_out=0.35, yaw=0.0):
    sx = 1 if s == "L" else -1
    side = Matrix.Rotation(math.radians(yaw), 3, "Z") @ V(sx, 0, 0)
    H.key_hand(s, f, W, d.normalized(), n.normalized(), pole=W + side * elbow_out + V(0, 0, -0.25))
    curl(H, s, f, 0.3)
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
_bA = D["MK_BodyA"]
_sv = max((v.co for v in _bA.data.vertices if abs(v.co.z - 0.30) < 0.02 and abs(v.co.y + 0.28) < 0.03), key=lambda c: c.x)
SHOULDER_W = M_LIE1 @ _sv
# beat 1: marker drawing 40-200, left hand steadies the head
for f in range(1, 252, 6):
    sw = 0.5 + 0.5 * math.sin(f / 24.0)
    pose(SURG, f, S0, Y0, flex=26 + 3 * sw, twist=-6, headr=(18, 4))
    a = A0 + (A1 - A0) * smooth((f - 60) / 140.0)
    tip = neck_ring(M_LIE1, a, 0.081) if f > 40 else neck_ring(M_LIE1, A0, 0.11) + V(0, -0.05, 0.08)
    if f > 205: tip = neck_ring(M_LIE1, A1, 0.11) + V(0.0, -0.08, 0.10 * smooth((f - 205) / 20))
    Wp = tip + V(0, -0.04, 0.13); Wp.z = max(Wp.z, NA.z + 0.13)
    hand(SURG, "R", f, Wp, V(0.1, 0.3, -1), V(1, 0, 0.2), 0.35, Y0)
    hand(SURG, "L", f, SHOULDER_W + V(0, 0, 0.07), V(0.4, 1, 0.18), V(0, 0, -1), 0.4, Y0)
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
FM = V(-0.385, -0.923, 0).normalized()
HC_M = EYEMID - FM * 0.045 + V(0, 0, 0.01)
hverts = [(v.co.copy(), v.normal.copy()) for v in head.data.vertices]
def surf(p):
    c, n = min(hverts, key=lambda cn: (cn[0] - p).length); return c, n
# left palm on the up-facing temple (model +X), fingers toward the crown; right hand cradles the back of the skull, fingers wrapping over
SL, NL = surf(HC_M + V(0.07, 0, 0.0)); DL = V(0, 0, 1)
SR, NR_ = surf(HC_M - FM * 0.075 + V(0, 0, -0.01)); DR = V(1, 0, 0.25).normalized()
GRIP_OFF = {"L": 0.03, "R": 0.03}; GRIP_CURL = {"L": 1.0, "R": 1.0}
def grip(f, S_, N_, D_, s):
    M = head_world(f) if f < 376 else M_root(f)
    R3 = M.to_3x3()
    Sw = M @ S_; Nw = (R3 @ N_).normalized(); Dw = R3 @ D_
    Dw = (Dw - Nw * Dw.dot(Nw)).normalized()
    W = Sw + Nw * GRIP_OFF[s] - Dw * 0.085
    return W, Dw, (-Nw if s == "L" else Nw)
def beat2_keys(frames):
    for f in frames:
        u = smooth((f - 290) / 60.0)
        pos = S0.lerp(S1, u); yw = Y0 + (Y1 - Y0) * u
        feet = {"L": (SURG.foot_xy("L", S0.lerp(S1, smooth((f - 290) / 30.0)), yw), yw), "R": (SURG.foot_xy("R", S0.lerp(S1, smooth((f - 318) / 30.0)), yw), yw)}
        lift = {s: 0.0 for s in "LR"}
        pose(SURG, f, pos + V(0, 0, 0), yw, flex=30 - 8 * math.sin(math.pi * smooth((f - 262) / 110)), twist=-4, headr=(20, 0), feet=feet)
        for s, (xy, yw_) in feet.items():
            ph0 = 290 if s == "L" else 318
            lf = 0.07 * math.sin(math.pi * max(0.0, min(1.0, (f - ph0) / 30.0)))
            SURG.key_foot(s, f, xy, yw_, lift=lf)
        ff = min(f, 384); app = 1 - smooth((f - 214) / 34.0); rel = smooth((f - 384) / 16.0)
        for s, (S_, N_, D_) in (("L", (SL, NL, DL)), ("R", (SR, NR_, DR))):
            W, d_, n_ = grip(ff, S_, N_, D_, s)
            Nw = ((head_world(ff) if ff < 376 else M_root(ff)).to_3x3() @ N_).normalized()
            W = W + Nw * 0.09 * max(app, rel) + V(0, -0.05, 0.04) * max(app, rel)
            hand(SURG, s, f, W, d_, n_, 0.4, yw)
            curl(SURG, s, f, GRIP_CURL[s] * (1.0 - max(app, rel)))

beat2_keys(list(range(214, 400, 3)) + [400])
# numeric grip search: back each hand off the head surface until the glove sits on the fur (no verts inside)
from mathutils.bvhtree import BVHTree as _BVH
_sb = D["Surgeon.body"]
_gi = [i for i, m in enumerate(_sb.data.materials) if m and m.name.startswith("M_Glove")][0]
_hand_v = {s_: sorted({v for p_ in _sb.data.polygons if p_.material_index == _gi for v in p_.vertices
                       if (_sb.data.vertices[v].co.x > 0) == (s_ == "L")}) for s_ in "LR"}
def _pen(f, s_):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    e = head.evaluated_get(dg); m = e.to_mesh(); hb = _BVH.FromPolygons([e.matrix_world @ v.co for v in m.vertices], [tuple(p_.vertices) for p_ in m.polygons]); e.to_mesh_clear()
    eb = _sb.evaluated_get(dg); mb = eb.to_mesh()
    n = 0; dmin = 9
    for i in _hand_v[s_][::2]:
        if i >= len(mb.vertices): continue
        p_ = eb.matrix_world @ mb.vertices[i].co
        loc, nrm, idx, d = hb.find_nearest(p_, 0.2)
        if loc is None: continue
        if (p_ - loc).dot(nrm) < -0.002: n += 1
        dmin = min(dmin, d)
    eb.to_mesh_clear(); return n, dmin
_mods_sb = [(md_, md_.show_viewport) for md_ in _sb.modifiers if md_.type != 'ARMATURE']
for md_, _ in _mods_sb: md_.show_viewport = False
for s_ in "LR":
    best = None
    for off in (0.03, 0.04, 0.05, 0.06, 0.07):
        for cu in (1.0, 0.75, 0.5):
            GRIP_OFF[s_] = off; GRIP_CURL[s_] = cu
            beat2_keys([300])
            n, dmin = _pen(300, s_)
            score = n * 10 + (0 if dmin < 0.012 else (dmin - 0.012) * 1000)
            if best is None or score < best[0]: best = (score, off, cu, n, dmin)
    GRIP_OFF[s_], GRIP_CURL[s_] = best[1], best[2]
    print("GRIPSEARCH", s_, "off", best[1], "curl", best[2], "inside", best[3], "nearest", round(best[4] * 100, 2), "cm")
for md_, v_ in _mods_sb: md_.show_viewport = v_
beat2_keys(list(range(214, 400, 3)) + [400])
# beat 3: stitching 400-665 - right hand needle holder arcs in at each stitch, left hand forceps holds the edge
stitch_ang = [2 * math.pi * i / len(st) for i in range(len(st))]
for f in list(range(403, 672, 3)):
    pose(SURG, f, S1, Y1, flex=34, twist=-3, headr=(24, -4))
    k = min((f - 395) // 26, len(STITCH_ORDER) - 1); ph = ((f - 395) % 26) / 26.0
    a = stitch_ang[STITCH_ORDER[k]] + 0.12
    seam_pt = neck_ring(M_LIE2, a, 0.074)
    arc = V(0.0, -0.03 * math.cos(2 * math.pi * ph), 0.03 * math.sin(2 * math.pi * ph))
    hand(SURG, "R", f, seam_pt + V(0.03, -0.13, 0.15) + arc, V(0.2, 0.6, -0.6), V(1, 0, 0.4), 0.35, Y1)
    hand(SURG, "L", f, neck_ring(M_LIE2, A_UP + 0.9, 0.09) + V(-0.07, -0.11, 0.15) + V(0, 0, 0.01 * math.sin(f / 9.0)), V(-0.1, 0.6, -0.6), V(-1, 0, 0.3), 0.35, Y1)
    curl(SURG, "R", f, 0.75); curl(SURG, "L", f, 0.6)
# beats 4-5: steps back, watches; snaps fingers near the ear at 920 (the "hear" cue together with the bowl)
S2 = V(0.25, -0.95, 0)
for f in list(range(672, 1040, 6)):
    ur = max(0.0, min(1.0, (f - 672) / 40.0)); u = smooth(ur)
    pos = S1.lerp(S2, u)
    pose(SURG, f, pos, Y1 - 10 * u, flex=18 - 8 * u, twist=6 * u, headr=(18, -6 + 12 * math.sin(f / 50.0)), step=(S1, Y1, S2, Y1 - 10, ur))
    if 890 < f < 960:
        k = smooth((f - 890) / 20.0) * (1 - smooth((f - 945) / 15.0))
        hang(SURG, "L", f, pos, Y1)
        hand(SURG, "R", f, V(0.48, -0.42, 1.25).lerp(V(0.3, -0.75, 1.0), 1 - k), V(0.3, 1, 0.5), V(1, 0, 0), 0.3, Y1)
    else:
        for s in "LR": hand(SURG, s, f, pos + Matrix.Rotation(math.radians(Y1), 3, "Z") @ V((0.08 if s == "L" else -0.08), -0.28, 0) + V(0, 0, 1.0), V(0, 1, 0.2) if False else Matrix.Rotation(math.radians(Y1), 3, "Z") @ V((-1 if s == "L" else 1), -0.3, 0), V(0, 0, 1), 0.3, Y1)
# beats 7-9: recovery corner. Surgeon beside the chair waves a hand in front of the monkey (no reaction), then clipboard at the monitor
S3 = V(1.62, 1.25, 0); Y3 = yaw_to(S3, CH + V(0, 0.2, 0))
S4 = V(2.6, 0.6, 0); Y4 = yaw_to(S4, V(3.05, 0.95, 0))
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
        ur = max(0.0, min(1.0, (f - 1380) / 40.0)); u = smooth(ur)
        pos = S3.lerp(S4, u); yw = Y3 + (Y4 - Y3) * u
        pose(SURG, f, pos, yw, flex=12 + 10 * smooth((f - 1600) / 80.0), headr=(18 + 14 * smooth((f - 1600) / 80.0), 0), step=(S3, Y3, S4, Y4, ur))
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
        curl(NURSE, s, f, 0.8)
NP2 = V(-0.85, -0.62, 0); ny2 = yaw_to(NP2, V(0.0, 0.05, 0))
NP2b = V(-0.80, 1.05, 0); ny2b = yaw_to(NP2b, V(-1.35, 1.25, 0))
WALKS = [(300, 400, NP2, NP2b), (560, 680, NP2b, NP2)]
def nurse_at(f):
    if f <= 300: return NP2, ny2
    for a0, a1, p0, p1 in WALKS:
        if a0 <= f <= a1:
            u = smooth((f - a0) / (a1 - a0)); return p0.lerp(p1, u), None
    if 400 < f < 560: return NP2b, ny2b
    return NP2, ny2
for a0, a1, p0, p1 in WALKS:
    hd = (p1 - p0).normalized(); yw_ = math.degrees(math.atan2(hd.x, -hd.y))
    NURSE.walk(lambda f, a0=a0, a1=a1, p0=p0, p1=p1: p0.lerp(p1, smooth((f - a0) / (a1 - a0))).to_3d(), lambda f, yw_=yw_: yw_, a0, a1, stride=0.55, duty=0.6, lift=0.07, bob=0.018, crouch=0.04, lean=6)
bowl = D["Bowl"]
for f in list(range(166, 1040, 6)):
    ur = max(0.0, min(1.0, (f - 166) / 40.0)); u = smooth(ur)
    walking = any(a0 <= f <= a1 for a0, a1, _, _ in WALKS)
    if f < 300:
        p = NP1.lerp(NP2, u); yw = ny + (ny2 - ny) * u
        pose(NURSE, f, p, yw, flex=10, headr=(12, 10 * math.sin(f / 60.0)), step=(NP1, ny, NP2, ny2, ur))
    else:
        p, yw = nurse_at(f)
        if yw is None:
            a0, a1, p0, p1 = next(w for w in WALKS if w[0] <= f <= w[1]); hd = (p1 - p0).normalized(); yw = math.degrees(math.atan2(hd.x, -hd.y))
        if not walking:
            pose(NURSE, f, p, yw, flex=10, headr=(12, 10 * math.sin(f / 60.0)))
    Rz = Matrix.Rotation(math.radians(yw), 3, "Z")
    if 440 < f < 520:   # turns the gas knob on the anaesthesia machine
        k = math.sin(math.pi * (f - 440) / 80.0)
        hand(NURSE, "R", f, (p + V(0, 0, 0.9) + Rz @ V(-0.15, -0.3, 0)).lerp(V(-1.25, 1.02, 0.92), k), Rz @ V(0, -1, 0), V(0, 0, 1), 0.3, yw)
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
NP3 = V(3.5, 0.55, 0); ny3 = yaw_to(NP3, V(3.05, 0.95, 0))
NDOOR = V(4.12, 2.75, 0)
NURSE.walk(lambda f: NP3.lerp(NDOOR, smooth((f - 1610) / 150.0)).to_3d(), lambda f: yaw_to(NP3, NDOOR), 1610, 1770, stride=0.6, duty=0.6, lift=0.07, bob=0.018, crouch=0.03, lean=5)
dpv = D["Door_Pivot"]; dpv.rotation_mode = "XYZ"
for f_, a_ in ((1, 0), (1660, 0), (1710, -82), (1770, -86)):
    dpv.rotation_euler.z = math.radians(a_); dpv.keyframe_insert("rotation_euler", frame=f_, index=2)
for f in list(range(1190, 1771, 6)):
    if f >= 1610:
        pN = NP3.lerp(NDOOR, smooth((f - 1610) / 150.0)); yN = yaw_to(NP3, NDOOR)
        hang(NURSE, "R", f, pN, yN, 0.08); hang(NURSE, "L", f, pN, yN, 0.08); continue
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
ANA = Human(make_human_ctrl(D["Anaes"]))
AP = V(-1.45, 0.62, 0); AY = yaw_to(AP, V(-1.3, 1.25, 0)); RzA = Matrix.Rotation(math.radians(AY), 3, "Z")
bag = D["Anaes_Bag"]; bag_c = bag.location.copy()
for f in list(range(1, 1771, 6)):
    br = 0.5 + 0.5 * math.sin(2 * math.pi * f / 150.0)
    ANA.key_root(f, V(AP.x, AP.y, 0.70), yaw=AY, flex=8)
    ANA.key_spine(f, flex=14, twist=-6, head=(14 + 6 * math.sin(f / 90.0), 18 * math.sin(f / 140.0)))
    for s in "LR":
        ANA.key_foot(s, f, ANA.foot_xy(s, V(AP.x, AP.y, 0), AY) + (RzA @ V(0, -0.42, 0)).to_2d(), AY + (10 if s == "L" else -10))
    hand(ANA, "R", f, bag_c + RzA @ V(-0.06, -0.09 + 0.02 * br, 0.0), RzA @ V(0.2, 1, 0), RzA @ V(-1, 0, 0), 0.3, AY)
    curl(ANA, "R", f, 0.4 + 0.5 * (1 - br))
    hand(ANA, "L", f, V(-1.30, 1.0, 0.93) + V(0, 0, 0.01 * math.sin(f / 30.0)), RzA @ V(0, 1, -0.4), V(0, 0, 1), 0.3, AY)
    bag.scale = (1.0 + 0.12 * br, 1.0 + 0.12 * br, 1.0 - 0.05 * br); bag.keyframe_insert("scale", frame=f)
for ob in [D["Anaes"]] + [c for c in D["Anaes"].children]:
    hide_keys(ob, [(1, False), (1036, True), (1187, False)])
# dust motes drift (and hide before the void fades in)
dr_ = D["Dust_Root"]
for f in range(1, 1771, 30):
    dr_.location = V(0.1 + 0.03 * math.sin(f / 170.0), 0.12 + 0.03 * math.cos(f / 210.0), 1.4 + 0.04 * math.sin(f / 260.0)); dr_.keyframe_insert("location", frame=f)
    dr_.rotation_euler.z = f / 900.0; dr_.keyframe_insert("rotation_euler", frame=f, index=2)
for o in D:
    if o.name.startswith("Dust_") and o.type == "MESH" and o.name != "Dust_Src":
        hide_keys(o, [(1, False), (1012, True), (1190, False)])
# head droop after the wave (3 deg about the neck centre, the seam ring covers the joint)
FMh = V(-0.385, -0.923, 0).normalized(); RTm = FMh.cross(V(0, 0, 1)).normalized()
for f_, a_ in ((1300, 0.0), (1345, 3.0), (1770, 3.4)):
    Md = Matrix.Translation(NC) @ Matrix.Rotation(math.radians(a_), 4, RTm) @ Matrix.Translation(-NC)
    l_, q_, _ = Md.decompose(); head.location = l_; head.keyframe_insert("location", frame=f_)
    head.rotation_quaternion = q_; head.keyframe_insert("rotation_quaternion", frame=f_)
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
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 5.6
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
 (290,  V(0.0, 1.05, 1.56), V(-0.05, -0.05, 1.12), 32, UPW, "W"),
 (330,  V(0.3, 1.0, 1.54), V(0.25, -0.05, 1.12), 32, UPW, "W"),
 (365,  V(0.95, 0.15, 1.45), NBp, 30, UPW, "W"),
 (420,  NBp + V(0.42, -0.05, 0.38), NBp, 75, UPW, "W"),
 (480,  NBp + V(0.42, -0.06, 0.2), NBp, 75, UPW, "W"),
 (540,  NBp + V(0.32, 0.18, 0.32), NBp, 75, UPW, "W"),
 (600,  NBp + V(0.42, 0.06, 0.06), NBp + V(0, 0, 0.03), 70, UPW, "W"),
 (650,  NBp + V(0.36, -0.16, 0.12), NBp + V(0.02, -0.02, 0.0), 60, UPW, "W"),
 (700,  FBp + FWW * 0.32 + V(0, -0.18, 0.08), FBp, 40, V(0, -0.6, 0.8), "W"),
 (760,  FBp + FWW * 0.24 + V(0, -0.08, 0.05), FBp, 52, V(0, -1, 0.05), "W"),
 (820,  FBp + FWW * 0.13 + V(0, -0.02, 0.02), FBp, 70, V(0, -1, 0.05), "W"),
 (880,  FBp + FWW * 0.18 + V(0, 0.06, 0.06), FBp, 55, V(0, -1, 0.05), "W"),
 (930,  FBp + FWW * 0.16 + V(0, 0.16, 0.12), FBp, 45, V(0, -1, 0.05), "W"),
 (975,  FBp + V(0.06, 0.14, 0.25), FBp + V(-0.02, 0.05, 0), 38, V(0, -1, 0.4), "W"),
 (1005, NBp + V(0.0, 0.02, 0.33), NBp + V(0, 0.03, 0), 34, V(0, -1, 0), "W"),
 (1030, NBp + V(0.0, 0.03, 0.22), NBp + V(0, 0.03, 0), 34, V(0, -1, 0), "W"),
 (1064, NC + V(0.24, 0.02, 0.0), NC + V(0, 0.02, -0.02), 34, V(0, 0, 1), "B"),
 (1110, V(0.24, -0.55, 0.32), V(-0.02, -0.28, 0.27), 28, V(0, 0, 1), "B"),
 (1160, V(-0.04, -0.66, 0.52), EYEMID + V(0.0, 0.05, -0.02), 32, V(0, 0, 1), "B"),
 (1190, V(-0.05, -0.80, 0.46), V(-0.05, -0.32, 0.32), 30, V(0, 0, 1), "B"),
 (1250, CH + V(-0.6, -1.35, 0.62), CH + V(0, 0.25, 0.62), 24, UPW, "W"),
 (1320, CH + V(0.35, -1.45, 0.85), CH + V(0.05, 0.2, 0.66), 26, UPW, "W"),
 (1380, V(2.85, -0.42, 1.08), V(2.95, 0.7, 0.95), 30, UPW, "W"),
 (1440, SCR + V(-0.06, -0.42, 0.05), SCR, 45, UPW, "W"),
 (1500, SCR + V(0.04, -0.24, 0.02), SCR, 50, UPW, "W"),
 (1560, SCR + V(0.24, -0.30, 0.09), SCR + V(-0.02, 0, 0), 40, UPW, "W"),
 (1620, V(3.45, -0.5, 1.4), V(2.5, 0.9, 0.75), 30, UPW, "W"),
 (1700, V(1.8, -2.1, 1.8), V(2.3, 0.9, 0.9), 24, UPW, "W"),
 (1770, V(1.6, -2.5, 1.95), V(2.2, 0.85, 0.9), 24, UPW, "W"),
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
for o in D:
    set_const(o)
    if o.type == "LIGHT": o.visible_camera = False; o.visible_glossy = False
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ANIM_SAVED", OUT)

if os.environ.get("GRIPDBG"):
    for f in (300,):
        sc.frame_set(f); r = D["Surgeon"]
        hv = [head.matrix_world @ v.co for v in head.data.vertices]
        for s in "LR":
            tip = r.matrix_world @ r.pose.bones["finger3-3." + s].tail
            print("GRIPDBG", s, CURL_SIGN, round(min((v - tip).length for v in hv) * 100, 1), "cm")
