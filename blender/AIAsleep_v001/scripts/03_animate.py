"""Animate AIAsleep: driver acting + face, world motion, cabin FX, one continuous camera.
blender -b work/scene.blend --python scripts/03_animate.py -- work/anim.blend"""
import sys, os, math, json, bpy
from mathutils import Vector, Matrix, Quaternion
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[sys.argv.index("--") + 1]
exec(open(os.path.join(HERE, "..", "pipeline", "anim_lib.py")).read())
sc = bpy.context.scene; O = bpy.data.objects
rig = O["Driver"]; R = Rig(rig); H = Human(R)
BEATS = [(1, 0.0, "As he drove, the car's AI scanned his face"), (2, 3.9, "flashed red, warning him to wake up"),
         (3, 6.9, "confused, because he wasn't sleeping"), (4, 10.1, "sat up straighter to look more alert"),
         (5, 13.0, "nothing worked until he forced his eyes wide open"), (6, 18.0, "The moment they relaxed, the alarm went off again"),
         (7, 21.7, "twenty times on a single trip"), (8, 24.4, "designed to beep whenever it couldn't see the iris"),
         (9, 28.8, "naturally had epicanthic folds"), (10, 36.9, "forming a smooth flap that covers part of the iris"),
         (11, 40.8, "making the AI think he was asleep")]
F = lambda t: int(round(1 + t * 60))
json.dump([{"beat": b, "frame": F(t), "first_words": w} for b, t, w in BEATS], open(os.path.join(HERE, "beats.json"), "w"), indent=1)
def K(o, path, f, v, idx=-1):
    setattr(o, path, v) if idx < 0 else getattr(o, path).__setitem__(idx, v)
    o.keyframe_insert(path, frame=f, index=idx)
def nkey(node_input, f, v):
    node_input.default_value = v; node_input.keyframe_insert("default_value", frame=f)

# ---------------- eyeball mesh follows head/eye bones only (lid bones were crumpling it)
eo = O["Driver.high-poly"]; hg = eo.vertex_groups.get("head") or eo.vertex_groups.new(name="head")
bad = [g for g in eo.vertex_groups if g.name.startswith(("orbicularis", "oculi", "levator", "temporalis", "special"))]
bidx = {g.index for g in bad}
for v in eo.data.vertices:
    w = sum(g.weight for g in v.groups if g.group in bidx)
    if w > 0: hg.add([v.index], w, "ADD")
for g in bad: eo.vertex_groups.remove(g)
# skin pores were too strong for the macros
sgp = next(n for n in bpy.data.materials["Driver.body"].node_tree.nodes if n.type == "GROUP")
sgp.inputs["Pore strength"].default_value = 0.06
# ---------------- driver: clear the seat pose from 02, rebuild per beat
rig.animation_data_clear() if False else None
import types
def seat(f, flex=-14, side=0.0, twist=0.0, head=(0.0, 0.0), dz=0.0, dy=0.0, spine=8.0):
    H.key_root(f, Vector((0, -0.07 + dy, 0.62 + dz)), flex=flex, side=side)
    H.key_spine(f, flex=spine, twist=twist, side=side * 0.5, head=head)
def face(f, lid=0.0, brow_knit=0.0, brow_up=0.0, jaw=0.0):
    for s in "LR":
        for n, ax, a in (("orbicularis03." + s, 'X', lid), ("orbicularis04." + s, 'X', -lid * 0.25), ("oculi02." + s, 'X', brow_knit), ("oculi01." + s, 'X', -brow_up)):
            pb = R.PB[n]; pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = Quaternion(Vector((1, 0, 0)), math.radians(a)); pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
    pb = R.PB["jaw"]; pb.rotation_quaternion = Quaternion(Vector((1, 0, 0)), math.radians(jaw)); pb.keyframe_insert("rotation_quaternion", frame=f, group="jaw")
def blink(f):
    face(f - 3, 0); face(f, -32); face(f + 4, 0)
WHEEL_C = Vector((0.0, -0.525, 0.92)); WHEEL_TILT = -66
def rim_point(ang, r=0.18):
    t = math.radians(WHEEL_TILT); a = math.radians(ang)
    up = Matrix.Rotation(t, 3, 'X') @ Vector((0, -1, 0)); right = Vector((-1, 0, 0))
    return WHEEL_C + up * (r * math.cos(a)) + right * (r * math.sin(a)), up, Matrix.Rotation(t, 3, 'X') @ Vector((0, 0, 1))
def hand(s, f, ang, lift=Vector((0, 0, 0)), k=1.0):
    p, up, nrm = rim_point(ang); rad = (p - WHEEL_C).normalized()
    W = p + rad * 0.058 + nrm * 0.049 + lift
    H.key_hand(s, f, W, (-nrm * 0.9 - rad * 0.3).normalized(), -nrm, pole=W + Vector((0.35 if s == "L" else -0.35, 0.4, -0.35)))
    grip(f, s, k)
def grip(f, s, k=1.0):
    for fi in (2, 3, 4, 5):
        for j, a in ((1, 55), (2, 70), (3, 45)):
            n = "finger%d-%d.%s" % (fi, j, s); pb = R.PB[n]
            pb.rotation_quaternion = Quaternion(Vector((1, 0, 0)), math.radians(a * k)); pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
    for j, a in ((1, 10), (2, 25), (3, 25)):
        n = "finger1-%d.%s" % (j, s); pb = R.PB[n]
        pb.rotation_quaternion = Quaternion(Vector((1, 0, 0)), math.radians(a * k)); pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
def hands(f, aL=-90, aR=90):
    hand("L", f, aL); hand("R", f, aR)
# timeline of acting -------------------------------------------------------
# beat 1: calm driving, micro head motion, small steering corrections (hands slide with the rim angle)
for f, hd, aL in ((1, (0, 0), -90), (60, (2, 3), -87), (120, (0, -2), -92), (180, (1, 1), -90), (234, (0, 0), -90)):
    seat(f, head=hd); hands(f, aL, -aL); face(f)
blink(95); blink(200)
# beat 2: red flash -> flinch back, look down to the screen
seat(250, flex=-17, head=(-6, 0), dy=0.02); face(250, lid=8, brow_up=10)
seat(300, flex=-15, head=(14, -22), twist=-6); face(300, lid=0, brow_knit=6)
seat(360, flex=-14, head=(12, -26), twist=-8); hands(360)
seat(414, flex=-14, head=(4, -10)); face(414, brow_knit=10)
# beat 3: confused: head tilt, brows knit, look screen <-> road, purse
seat(460, flex=-14, side=6, head=(6, -24)); face(460, brow_knit=16, jaw=2)
seat(520, flex=-14, side=-4, head=(-2, 6)); face(520, brow_knit=12, brow_up=6)
seat(575, flex=-14, side=5, head=(8, -28)); face(575, brow_knit=18, jaw=3)
blink(540); seat(606, flex=-14, side=2, head=(2, -8)); face(606, brow_knit=10)
# beat 4: sits up straighter: spine extends, rises 3 cm, head shake, re-grip
seat(640, flex=-6, spine=0, dz=0.03, dy=-0.02, head=(-4, 0)); face(640, lid=6, brow_up=8)
for i, f in enumerate(range(660, 720, 10)):
    seat(f, flex=-6, spine=0, dz=0.03, dy=-0.02, head=(-2, 14 * (1 if i % 2 else -1)))
seat(720, flex=-5, spine=-2, dz=0.035, dy=-0.03, head=(-3, 0))
hand("L", 690, -92, Vector((0, 0.02, 0.05)), 0.3); hand("R", 690, 92, Vector((0, 0.02, 0.05)), 0.3)
hands(712, -88, 88); seat(780, flex=-5, spine=-2, dz=0.035, dy=-0.03, head=(-2, -4)); face(780, lid=4)
# beat 5: tries: nod, hard blink, then forced wide eyes; screen goes green ~f960
seat(820, flex=-5, spine=-2, dz=0.035, dy=-0.03, head=(10, 0)); face(820, lid=-10)
seat(850, flex=-5, spine=-2, dz=0.035, dy=-0.03, head=(-6, 0)); face(840, lid=-34); face(852, lid=6)
blink(880)
seat(910, flex=-6, spine=-3, dz=0.04, dy=-0.04, head=(-8, -6)); face(905, lid=4, brow_up=6)
face(930, lid=30, brow_up=30, jaw=1); face(1000, lid=32, brow_up=32, jaw=2); face(1080, lid=31, brow_up=30, jaw=1)
seat(1000, flex=-6, spine=-3, dz=0.04, dy=-0.05, head=(-6, -14)); seat(1080, flex=-6, spine=-3, dz=0.04, dy=-0.05, head=(-5, -4))
hands(1000, -90, 90)
# beat 6: eyes relax -> red again; slump, frustrated exhale, right hand gesture off the wheel
face(1100, lid=0, brow_up=0); seat(1110, flex=-14, spine=8, head=(0, -6))
face(1150, brow_knit=20, jaw=8); seat(1160, flex=-18, spine=12, dz=-0.015, head=(-10, 0), side=-3)
hand("R", 1180, 90); hand("R", 1205, 70, Vector((-0.10, 0.14, 0.12)), 0.2); hand("R", 1240, 70, Vector((-0.08, 0.12, 0.10)), 0.25); hand("R", 1265, 90)
face(1215, brow_knit=18, jaw=3); seat(1230, flex=-16, spine=10, head=(4, -20)); seat(1302, flex=-15, spine=8, head=(0, 0)); face(1302, brow_knit=12)
hand("L", 1265, -90)
# beat 7..: steady driving with breathing and occasional blinks
for f in (1380, 1464, 1560, 1650, 1729, 1900, 2100, 2300, 2449): seat(f, head=(0, (f % 3 - 1) * 1.5)); face(f, brow_knit=4)
hands(1380); hands(1729); hands(2449)
blink(1420); blink(1655)
# beat 11: sigh, slow head shake
seat(2500, flex=-17, spine=11, head=(-8, 0), dz=-0.01); face(2500, brow_knit=14, jaw=6)
seat(2545, flex=-16, spine=10, head=(2, 10)); seat(2580, flex=-16, spine=10, head=(2, -10)); seat(2610, flex=-15, spine=9, head=(0, 0)); face(2610, brow_knit=8)
for s in "LR": pass
# feet planted all film
def feet(f):
    for s, x in (("L", 0.13), ("R", -0.13)):
        a = H.ankle[s]
        M = Matrix.Translation(Vector((x, -0.80, 0.37))) @ Matrix.Rotation(math.radians(-22), 4, 'X') @ Matrix.Translation(-a) @ R.rest("IK_foot." + s)
        R.key_world("IK_foot." + s, f, M)
feet(1); feet(2610)

# ---------------- world motion: everything outside slides +Y (car speed 27 m/s; 6x time-lapse in beat 7)
mover = O["WorldMover"]; d = 0.0; spd = lambda f: 27.0 * (1 + 5 * smooth((f - 1303) / 40) * (1 - smooth((f - 1425) / 40)))
mover.animation_data_clear()
for f in range(1, 2611, 10):
    K(mover, "location", f, d, 1)
    for g in range(f, f + 10): d += spd(g) / 60.0
for fc in mover.animation_data.action.fcurves if hasattr(mover.animation_data.action, "fcurves") else []:
    for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
# city skyline parallax: 10% of road speed
for o, base in ((O["CityRoot"], -150), (O["CityInst"], -600)):
    K(o, "location", 1, base, 1); K(o, "location", 2610, base + d * 0.10, 1)
# traffic: A overtakes us in the left lane during beat 1, B passes slowly through 3-6; both cycle by again in 7 and 11
for o, keys in ((O["TrafficA"], [(1, 14), (234, -16), (400, -60)]), (O["TrafficB"], [(300, 30), (800, -8), (1300, -40), (1303, 60), (1464, -80), (2449, 25), (2610, -12)])):
    for f, y in keys: K(o, "location", f, y, 1)
wn = sc.world.node_tree; WN = wn.nodes
lp = WN.new("ShaderNodeLightPath"); grad = WN.new("ShaderNodeTexCoord"); sepw = WN.new("ShaderNodeSeparateXYZ"); wn.links.new(grad.outputs["Generated"], sepw.inputs[0])
rampw = WN.new("ShaderNodeValToRGB"); rampw.color_ramp.elements[0].color = (0.06, 0.035, 0.03, 1); rampw.color_ramp.elements[0].position = 0.49
rampw.color_ramp.elements[1].color = (0.004, 0.006, 0.02, 1); rampw.color_ramp.elements[1].position = 0.62
wn.links.new(sepw.outputs["Z"], rampw.inputs[0]); bgc = WN.new("ShaderNodeBackground"); wn.links.new(rampw.outputs[0], bgc.inputs[0]); bgc.inputs[1].default_value = 1.0
mixw = WN.new("ShaderNodeMixShader"); wn.links.new(lp.outputs["Is Camera Ray"], mixw.inputs[0])
outw = next(n for n in WN if n.type == "OUTPUT_WORLD"); wn.links.new(WN["WorldBG"].outputs[0], mixw.inputs[1]); wn.links.new(bgc.outputs[0], mixw.inputs[2]); wn.links.new(mixw.outputs[0], outw.inputs[0])
# world HDRI rotation: slow drift so the city lights slide across the windows
wr = sc.world.node_tree.nodes["WorldRot"].inputs["Rotation"]
wr.default_value = (0, 0, 0); wr.keyframe_insert("default_value", frame=1, index=2)
wr.default_value = (0, 0, math.radians(140)); wr.keyframe_insert("default_value", frame=2610, index=2)

# ---------------- cabin FX timeline: screen state (0 red icon, 1 green), alarm pulses, scan beam
ui = bpy.data.materials["ScreenUI"].node_tree.nodes; uim = ui["UI_GREEN"].inputs[0]; uie = ui["Principled BSDF"].inputs["Emission Strength"]
red = O["Alarm_Red"].data; grn = O["Calm_Green"].data
def screen(f, green, e):
    nkey(uim, f, green); nkey(uie, f, e)
def pulse_red(f0, n, period=22, e=26):
    for i in range(n):
        f = f0 + i * period
        K(red, "energy", f, e); K(red, "energy", f + period // 2, e * 0.15); screen(f, 0.0, 9.0); screen(f + period // 2, 0.0, 2.5)
screen(1, 1.0, 0.0); K(red, "energy", 1, 0); K(grn, "energy", 1, 0)
screen(225, 1.0, 0.0); screen(236, 0.0, 9.0)
pulse_red(236, 16)                       # beats 2-4 alarm
pulse_red(781, 7)                        # beat 5 attempts still red
K(red, "energy", 940, 4); K(red, "energy", 958, 0); screen(950, 0.0, 3.0); screen(962, 1.0, 7.0); K(grn, "energy", 950, 0); K(grn, "energy", 965, 9); K(grn, "energy", 1090, 9)
K(grn, "energy", 1100, 0); screen(1095, 1.0, 7.0); screen(1102, 0.0, 9.0); pulse_red(1102, 9)
pulse_red(1310, 8, period=19, e=30)     # time-lapse: rhythmic flashes
K(red, "energy", 1470, 0); screen(1470, 0.0, 2.0)
pulse_red(2455, 7, period=22, e=20)
# scan beam sweeps (beat 1 and IR beat 8): rotate the slit spot up/down across the face
sb = O["ScanBeam"]; sbd = sb.data
sb.rotation_euler = (math.radians(-90), 0, 0)
for f0, f1, e in ((20, 234, 1.2), (1545, 1728, 0.8)):
    K(sbd, "energy", f0 - 1, 0.0); K(sbd, "energy", f0 + 6, e); K(sbd, "energy", f1 - 6, e); K(sbd, "energy", f1, 0.0)
    for i, f in enumerate(range(f0, f1, 36)):
        K(sb, "rotation_euler", f, math.radians(-90 + (14 if i % 2 else -14)), 0)
K(sbd, "energy", 1, 0.0)
lensm = bpy.data.materials["LensGlass"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
nkey(lensm, 1, 0.0); nkey(lensm, 20, 3.0); nkey(lensm, 234, 3.0); nkey(lensm, 250, 0.5)
# side window rolled down (the camera enters through it)
for o in O:
    if "Glass_Side_Front" in o.name: o.hide_render = True

# ---------------- one camera: location + aim keys (Bezier auto = continuous velocity), lens keys
camd = bpy.data.cameras.new("FilmCam"); cam = O.new("FilmCam", camd); sc.collection.objects.link(cam); sc.camera = cam
camd.clip_start = 0.004; camd.sensor_width = 24
aim = O.new("CamAim", None); sc.collection.objects.link(aim)
tt = cam.constraints.new("TRACK_TO"); tt.target = aim; tt.track_axis = "TRACK_NEGATIVE_Z"; tt.up_axis = "UP_Y"
sc.frame_set(1800); bpy.context.view_layer.update()
EYE = rig.matrix_world @ R.PB["eye.R"].head; print("EYE", EYE); DLT = EYE - Vector((-0.0295, -0.031, 1.31)); FACE = Vector((0, -0.06, 1.28)) + DLT; SCR = O["DashScreen"].matrix_world.translation.copy(); LENS = O["DashCamLens"].matrix_world.translation.copy()
INNER = EYE + Vector((0.016, -0.004, -0.002))   # inner corner (medial canthus) of his right eye, toward the nose
CAR = Vector((-0.37, -0.55, 0.8))
V = Vector
SHOTS = [  # frame, camera position, aim point, focal length
 (1,    V((1.9, -1.2, 0.75)),  V((0.1, -0.2, 1.05)), 24),
 (60,   V((1.15, -0.35, 1.10)), FACE, 26),
 (120,  V((0.32, -0.42, 1.20)), FACE, 28),
 (180,  V((0.08, -0.72, 1.14)), FACE, 24),
 (234,  V((-0.06, -0.42, 1.22)), FACE, 35),
 (270,  V((-0.26, -0.44, 1.17)), SCR, 30),
 (335,  V((-0.36, -0.50, 1.10)), SCR, 32),
 (414,  V((-0.76, -0.08, 1.24)), V((0, -0.3, 1.0)), 18),
 (480,  V((-0.50, -0.34, 1.15)), FACE, 40),
 (545,  V((-0.24, -0.52, 1.26)), FACE, 45),
 (606,  V((-0.10, -0.50, 1.26)), EYE, 50),
 (660,  V((-0.38, 0.75, 1.30)), V((0, -0.4, 1.1)), 24),
 (720,  V((-0.72, -0.15, 1.24)), V((0, 0.0, 1.1)), 22),
 (780,  V((-0.26, -0.50, 1.12)), FACE, 26),
 (840,  V((-0.22, -0.45, 1.18)), FACE, 30),
 (930,  V((-0.08, -0.30, 1.31)), EYE, 50),
 (980,  V((-0.30, -0.40, 1.17)), SCR, 35),
 (1080, V((-0.45, -0.62, 1.13)), FACE, 42),
 (1140, V((0.34, -0.20, 1.25)), FACE, 38),
 (1220, V((-0.25, 0.38, 1.32)), SCR, 28),
 (1302, V((-0.32, -0.04, 1.31)), V((0, -0.3, 0.9)), 20),
 (1340, V((-0.36, -0.02, 1.95)), CAR, 20),
 (1400, V((-1.6, 9.5, 4.2)), CAR, 24),
 (1464, V((3.6, -7.8, 1.9)), CAR, 28),
 (1500, V((0.0, -1.75, 1.16)), FACE, 30),
 (1528, V((0.0, -0.86, 1.10)), FACE, 30),
 (1550, V((0.0, -0.70, 1.11)), FACE, 32),
 (1620, V((0.0, -0.36, 1.27)), FACE, 40),
 (1680, V((-0.03, -0.16, 1.29)), EYE, 60),
 (1728, V((0.01, -0.13, 1.30)), EYE, 55),
 (1790, EYE + V((-0.005, -0.085, 0.004)), INNER, 40),
 (1830, EYE + V((0.000, -0.050, 0.002)), INNER, 40),
 (1900, EYE + V((-0.030, -0.060, 0.012)), INNER, 35),
 (1980, EYE + V((-0.012, -0.050, 0.028)), INNER, 35),
 (2060, EYE + V((-0.035, -0.055, -0.010)), INNER, 35),
 (2140, EYE + V((-0.004, -0.048, 0.006)), INNER, 40),
 (2214, EYE + V((-0.018, -0.058, 0.010)), INNER + V((0.004, 0, 0)), 40),
 (2260, EYE + V((-0.006, -0.080, 0.003)), EYE, 40),
 (2350, EYE + V((-0.002, -0.070, 0.000)), EYE, 40),
 (2448, EYE + V((-0.030, -0.075, 0.006)), EYE + V((0.002, 0, 0)), 35),
 (2510, V((-0.12, -0.46, 1.22)), FACE, 35),
 (2560, V((-0.32, 0.55, 1.28)), FACE, 24),
 (2610, V((-0.40, 6.5, 2.3)), CAR, 28),
]
for f, p, a, l in SHOTS:
    if (a is FACE or a is EYE) and f < 1780: p = p + DLT * 0.8
    K(cam, "location", f, p); K(aim, "location", f, a); K(camd, "lens", f, l)
def fcs(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    try: return list(ad.action.fcurves)
    except AttributeError:
        return [fc for l in ad.action.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
for idb in (cam, aim, camd):
    for fc in fcs(idb):
        for kp in fc.keyframe_points: kp.interpolation = "BEZIER"; kp.handle_left_type = kp.handle_right_type = "AUTO"
for fc in fcs(mover):
    for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
camd.dof.use_dof = True; camd.dof.focus_object = aim; camd.dof.aperture_fstop = 4.0
for f, v in ((1, 4.0), (1700, 4.0), (1760, 18.0), (2448, 18.0), (2500, 4.0)): K(camd.dof, "aperture_fstop", f, v)
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
# ---------------- look fixes: dark brown irises, black hair, warmer skin
eg = next(n for n in bpy.data.materials["Driver.high-poly"].node_tree.nodes if n.type == "GROUP")
eg.inputs["IrisMajorColor"].default_value = (0.09, 0.045, 0.02, 1); eg.inputs["IrisMinorColor"].default_value = (0.03, 0.015, 0.008, 1)
hm = bpy.data.materials["Driver.short02"].node_tree.nodes["Principled BSDF"]
hn = bpy.data.materials["Driver.short02"].node_tree
hmix = hn.nodes.new("ShaderNodeMix"); hmix.data_type = "RGBA"; hmix.blend_type = "MULTIPLY"; hmix.inputs[0].default_value = 1.0; hmix.inputs[7].default_value = (0.06, 0.05, 0.045, 1)
src = hm.inputs["Base Color"].links[0].from_socket if hm.inputs["Base Color"].links else None
if src: hn.links.new(src, hmix.inputs[6]); hn.links.new(hmix.outputs[2], hm.inputs["Base Color"])
else: hm.inputs["Base Color"].default_value = (0.02, 0.018, 0.016, 1)
sg = next(n for n in bpy.data.materials["Driver.body"].node_tree.nodes if n.type == "GROUP")
sg.inputs["colorMixIn"].default_value = (0.80, 0.52, 0.32, 1); sg.inputs["colorMixInStrength"].default_value = 0.22
# ---------------- AI overlays: face-landmark mesh, tracking box, iris detection circle
fx = bpy.data.collections.new("AIOverlay"); sc.collection.children.link(fx)
def emis(name, col, strength=4.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL": N.remove(n)
    e = N.new("ShaderNodeEmission"); e.inputs[0].default_value = (*col, 1); e.inputs[1].default_value = strength
    t = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader"); mx.name = "VIS"; mx.inputs[0].default_value = 0.0
    if name == "FaceMeshMat":   # only the face (front of the head), never the scalp
        tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sp.inputs[0])
        lt = N.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = -0.035; nt.links.new(sp.outputs["Y"], lt.inputs[0])
        gt = N.new("ShaderNodeMath"); gt.operation = "LESS_THAN"; gt.inputs[1].default_value = 1.37; nt.links.new(sp.outputs["Z"], gt.inputs[0])
        m1 = N.new("ShaderNodeMath"); m1.operation = "MULTIPLY"; nt.links.new(lt.outputs[0], m1.inputs[0]); nt.links.new(gt.outputs[0], m1.inputs[1])
        vv = N.new("ShaderNodeValue"); vv.name = "VISVAL"; m2 = N.new("ShaderNodeMath"); m2.operation = "MULTIPLY"
        nt.links.new(m1.outputs[0], m2.inputs[0]); nt.links.new(vv.outputs[0], m2.inputs[1]); nt.links.new(m2.outputs[0], mx.inputs[0])
        nt.links.new(t.outputs[0], mx.inputs[1]); nt.links.new(e.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], N["Material Output"].inputs[0])
        return m, vv.outputs[0], e.inputs[0]
    nt.links.new(t.outputs[0], mx.inputs[1]); nt.links.new(e.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], N["Material Output"].inputs[0])
    return m, mx.inputs[0], e.inputs[0]
body = O["Driver.body"]; fm = body.copy(); fm.data = body.data; fm.name = "FaceMeshOverlay"; fx.objects.link(fm)
for m_ in list(fm.modifiers):
    if m_.type not in ("ARMATURE",): fm.modifiers.remove(m_)
vg = next((g.name for g in body.vertex_groups if g.name == "head"), None)
if vg: mk = fm.modifiers.new("mask", "MASK"); mk.vertex_group = vg
dp = fm.modifiers.new("disp", "DISPLACE"); dp.strength = 0.0025; dp.mid_level = 0.0
wf = fm.modifiers.new("wire", "WIREFRAME"); wf.thickness = 0.0005; wf.use_replace = True
M_fm, fm_vis, _ = emis("FaceMeshMat", (0.2, 0.95, 1.0), 1.2); fm.data = fm.data  # shares mesh: use material override via slot link
fm.material_slots[0].link = "OBJECT"; fm.material_slots[0].material = M_fm
for o_ in fm.material_slots[1:]: o_.link = "OBJECT"; o_.material = M_fm
def vis(sock, f, v): sock.default_value = v; sock.keyframe_insert("default_value", frame=f)
for f, v in ((1, 0), (40, 0), (55, 0.45), (75, 0.1), (100, 0.4), (130, 0.05), (160, 0.4), (225, 0.2), (236, 0), (1540, 0), (1556, 0.22), (1720, 0.15), (1740, 0)):
    vis(fm_vis, f, v)
# tracking box + iris circle, bone-parented to the head so they ride with him
sc.frame_set(1); bpy.context.view_layer.update()
def curve_obj(name, pts, cyclic=True):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.00035
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts): sp.points[i].co = (*p, 1)
    sp.use_cyclic_u = cyclic; o = O.new(name, cu); fx.objects.link(o); return o
eye0 = rig.matrix_world @ R.PB["eye.R"].head
hb = R.PB["head"]
def parent_head(o):
    mw = o.matrix_world.copy(); o.parent = rig; o.parent_type = "BONE"; o.parent_bone = "head"
    bpy.context.view_layer.update(); o.matrix_world = mw
c0 = eye0 + Vector((0.0, -0.016, 0.0))
bx = curve_obj("TrackBox", [(c0.x - 0.022, c0.y, c0.z - 0.012), (c0.x + 0.022, c0.y, c0.z - 0.012), (c0.x + 0.022, c0.y, c0.z + 0.014), (c0.x - 0.022, c0.y, c0.z + 0.014)])
ci = curve_obj("IrisCircle", [(c0.x + 0.0062 * math.cos(a), c0.y - 0.001, c0.z + 0.0062 * math.sin(a)) for a in [i * 2 * math.pi / 48 for i in range(48)]])
M_box, box_vis, _ = emis("TrackBoxMat", (0.25, 1.0, 0.5), 5.0); bx.data.materials.append(M_box)
M_ci, ci_vis, ci_col = emis("IrisCircleMat", (0.25, 1.0, 0.5), 6.0); ci.data.materials.append(M_ci)
for o_ in (bx, ci): parent_head(o_)
for f, v in ((1, 0), (1580, 0), (1600, 1), (1745, 1), (1765, 0), (2270, 0), (2290, 1), (2448, 1), (2470, 0)): vis(box_vis, f, v)
for f, v in ((1, 0), (1640, 0), (1652, 1), (1745, 1), (1765, 0), (2270, 0), (2280, 1), (2448, 1), (2470, 0)): vis(ci_vis, f, v)
GREEN, RED = (0.25, 1.0, 0.5, 1), (1.0, 0.08, 0.05, 1)
def ccol(f, c): ci_col.default_value = c; ci_col.keyframe_insert("default_value", frame=f)
ccol(1, GREEN); ccol(1652, GREEN); ccol(1660, RED); ccol(1668, GREEN)    # blink at 1655 -> red
fl = 2290
while fl < 2448:   # beat 10: detection fails and flickers
    ccol(fl, RED); ccol(fl + 5, RED); ccol(fl + 6, GREEN); ccol(fl + 8, GREEN); ccol(fl + 9, RED); fl += 23
for fc in fcs(M_ci.node_tree):
    for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"
# ---------------- AI's-eye infrared grade (compositor), on while the camera is "inside" the dash camera
try:
    ng = bpy.data.node_groups.new("Grade", "CompositorNodeTree"); sc.compositing_node_group = ng
    N = ng.nodes; Lk = ng.links
    rl = N.new("CompositorNodeRLayers"); go = N.new("NodeGroupOutput"); ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    bw = N.new("CompositorNodeRGBToBW")
    tint = N.new("ShaderNodeMix") if False else N.new("CompositorNodeMixRGB") if hasattr(bpy.types, "CompositorNodeMixRGB") else N.new("ShaderNodeMix")
    print("MIXNODE", tint.bl_idname)
    if tint.bl_idname == "ShaderNodeMix":
        tint.data_type = "RGBA"; tint.blend_type = "MULTIPLY"; tint.inputs[0].default_value = 1.0
        Lk.new(bw.outputs[0], tint.inputs[6]); tint.inputs[7].default_value = (0.75, 1.0, 0.95, 1); tout = tint.outputs[2]
        mixn = N.new("ShaderNodeMix"); mixn.data_type = "RGBA"; Lk.new(rl.outputs["Image"], mixn.inputs[6]); Lk.new(tout, mixn.inputs[7]); fac = mixn.inputs[0]; mout = mixn.outputs[2]
    else:
        tint.blend_type = "MULTIPLY"; Lk.new(bw.outputs[0], tint.inputs[1]); tint.inputs[2].default_value = (0.75, 1.0, 0.95, 1); tout = tint.outputs[0]
        mixn = N.new("CompositorNodeMixRGB"); Lk.new(rl.outputs["Image"], mixn.inputs[1]); Lk.new(tout, mixn.inputs[2]); fac = mixn.inputs[0]; mout = mixn.outputs[0]
    Lk.new(rl.outputs["Image"], bw.inputs[0]); Lk.new(mout, go.inputs[0])
    for f, v in ((1, 0), (1532, 0), (1538, 1), (1740, 1), (1752, 0)): fac.default_value = v; fac.keyframe_insert("default_value", frame=f)
    sc.render.use_compositing = True; sc.render.compositor_device = "CPU"
    print("GRADE OK")
except Exception as ex:
    print("GRADE FAIL", ex)
bpy.ops.wm.save_as_mainfile(filepath=out); print("SAVED", out)
