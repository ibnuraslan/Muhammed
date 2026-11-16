"""B14 MomLiftsCar: characters, animation (each beat a clip in its own window, at 1x), cameras + markers.
blender -b work/sets.blend --python 03_anim.py -- out.blend"""
import bpy, sys, math, random, bmesh
from mathutils import Vector, Matrix, Quaternion, Euler
W = "/tmp/claude-0/b14/"; P = "/home/user/Muhammed/blender/pipeline/"; BRAND = "/home/user/Muhammed/blender/assets/brand/"
OUT = sys.argv[sys.argv.index("--") + 1]
exec(open(P + "anim_lib.py").read()); exec(open(P + "hand_poses.py").read())
sc = bpy.context.scene; R_ = math.radians
CUR_WIN = None; RIGS = {}; HUM = {}
exec(open(W + "scripts/lib_anim.py").read())
exec(open(W + "scripts/lib_sets.py").read().split("def logo_mat")[0])
random.seed(7)
F_END = 2200
sc.frame_start, sc.frame_end = 1, 2240
FLOORS = [bpy.data.objects["Driveway"]]
def gz(x, y): return 0.04

def ease(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def interp(keys, f):
    """piecewise smoothstep through (frame, value) keys"""
    if f <= keys[0][0]: return keys[0][1]
    for (fa, va), (fb, vb) in zip(keys, keys[1:]):
        if f <= fb: return va + (vb - va) * ease((f - fa) / (fb - fa))
    return keys[-1][1]

def lying_root(H, f, pos, yaw=90.0, roll=0.0):
    """root for a body lying on its back: face up, head toward -X (yaw 90)"""
    Rw = Matrix.Rotation(R_(yaw), 3, 'Z') @ Matrix.Rotation(R_(-90), 3, 'X') @ Matrix.Rotation(R_(roll), 3, 'Y')
    M = Matrix.Translation(pos) @ Rw.to_4x4() @ Matrix.Translation(-H.root_head) @ H.r.rest("root")
    H.r.key_world("root", f, M)

# ================================================================== characters
def two_tone(rig, key, top_rgb, bottom_rgb=None, dots=False, top_fac=0.9, bot_fac=0.8):
    """recolour a one-piece MPFB suit: top above the waist (rest/generated z), bottom below; optional white polka dots on the top"""
    suit = next(o for o in rig.children if key in o.name)
    zs = [v.co.z for v in suit.data.vertices]; z0, z1 = min(zs), max(zs)
    waist = (rig.data.bones["spine05"].head_local.z + rig.data.bones["spine04"].head_local.z) / 2 if "spine05" in rig.data.bones else 1.0
    cut = (waist - z0) / (z1 - z0); print("TWO_TONE", suit.name, round(z0, 3), round(z1, 3), round(waist, 3), round(cut, 3))
    for i, m in enumerate(suit.data.materials):
        if not m: continue
        m = m.copy(); suit.data.materials[i] = m; nt = m.node_tree
        P_ = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
        lk = P_.inputs["Base Color"].links[0]; src = lk.from_socket
        tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sp.inputs[0])
        top = nt.nodes.new("ShaderNodeMath"); top.operation = 'GREATER_THAN'; top.inputs[1].default_value = cut; nt.links.new(sp.outputs["Z"], top.inputs[0])
        bw = nt.nodes.new("ShaderNodeRGBToBW"); nt.links.new(src, bw.inputs[0])
        shade = nt.nodes.new("ShaderNodeMapRange"); shade.inputs["From Min"].default_value = 0.0; shade.inputs["From Max"].default_value = 0.5
        shade.inputs["To Min"].default_value = 0.6; shade.inputs["To Max"].default_value = 1.1; nt.links.new(bw.outputs[0], shade.inputs[0])
        def shaded(rgb):
            mm = nt.nodes.new("ShaderNodeMix"); mm.data_type = 'RGBA'; mm.blend_type = 'MULTIPLY'; mm.inputs['Factor'].default_value = 1.0
            cc = nt.nodes.new("ShaderNodeCombineColor"); nt.links.new(shade.outputs[0], cc.inputs[0]); nt.links.new(shade.outputs[0], cc.inputs[1]); nt.links.new(shade.outputs[0], cc.inputs[2])
            nt.links.new(cc.outputs[0], mm.inputs['A']); mm.inputs['B'].default_value = (*rgb, 1); return mm.outputs['Result']
        topc = shaded(top_rgb)
        if dots:
            vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 15.0; vor.inputs["Randomness"].default_value = 0.0
            mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (0.5, 0.25, 1.36)
            nt.links.new(tc.outputs["Generated"], mp.inputs[0]); nt.links.new(mp.outputs[0], vor.inputs["Vector"])
            dot = nt.nodes.new("ShaderNodeMath"); dot.operation = 'LESS_THAN'; dot.inputs[1].default_value = 0.26; nt.links.new(vor.outputs["Distance"], dot.inputs[0])
            md = nt.nodes.new("ShaderNodeMix"); md.data_type = 'RGBA'; nt.links.new(dot.outputs[0], md.inputs['Factor'])
            nt.links.new(topc, md.inputs['A']); md.inputs['B'].default_value = (0.96, 0.95, 0.93, 1); topc = md.outputs['Result']
        botc = shaded(bottom_rgb) if bottom_rgb else src
        tf = nt.nodes.new("ShaderNodeMix"); tf.data_type = 'RGBA'; nt.links.new(top.outputs[0], tf.inputs['Factor'])
        if bottom_rgb is None:
            nt.links.new(src, tf.inputs['A'])
        else:
            nt.links.new(botc, tf.inputs['A'])
        nt.links.new(topc, tf.inputs['B'])
        nt.links.new(tf.outputs['Result'], P_.inputs["Base Color"])

rigM, RM, HM = setup("MomB", "Mom")
two_tone(rigM, "female_casualsuit01", (0.78, 0.06, 0.09), None, dots=True)       # red polka-dot blouse (reference), jeans stay blue
rigS, RS, HS = setup("SonB", "Son")
two_tone(rigS, "male_casualsuit04", (0.92, 0.92, 0.90), (0.22, 0.26, 0.40))       # white T-shirt, dark blue trousers
rigX, RX, HX = setup("ManE", "Man")
two_tone(rigX, "male_casualsuit04", (1.0, 0.80, 0.08), (0.30, 0.36, 0.18))        # yellow T-shirt, olive trousers (reference), logo added below

# ================================================================== B1 + B2a: the lift (frames 1..780, one continuous action at 1x)
piv = bpy.data.objects["CarPivot"]; REAR = sc["car_rear_y"]
def _anc(o):
    while o.parent: o = o.parent
    return o
car_meshes = [o for o in bpy.data.objects if o.type == 'MESH' and _anc(o).name == "CarPivot" and o.name.startswith("Object_")]
print("CAR_MESHES", [o.name for o in car_meshes])
LIFT = [(1, 0.0), (50, 0.0), (90, 0.4), (230, 3.1), (300, 3.3), (420, 3.2), (560, 3.5), (780, 3.4)]   # degrees about the front axle
for f in range(1, 781, 5):
    th = interp(LIFT, f) + (0.08 * math.sin(f * 0.9) if f > 230 else 0.0)                  # small strain tremble at the top
    piv.rotation_euler.x = R_(th); piv.keyframe_insert("rotation_euler", index=0, frame=f)
bpy.context.view_layer.update()

def ray_up(x, y, f):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); best = None
    for o in car_meshes:
        oe = o.evaluated_get(dg); inv = oe.matrix_world.inverted()
        hit, loc, nrm, idx = oe.ray_cast(inv @ Vector((x, y, 0.06)), (inv.to_3x3() @ Vector((0, 0, 1))).normalized())
        if hit:
            z = (oe.matrix_world @ loc).z
            if best is None or z < best: best = z
    return best
# bumper underside profile at rest
for yy in [REAR - 0.02 * i for i in range(0, 20)]:
    print("BUMPER_UNDER y=%.2f z=%s" % (yy, ray_up(0.30, yy, 1)))
HY = REAR - 0.045
# Mom: deadlift squat behind the rear bumper, facing the car (-Y)
FOOT_Y = REAR + 0.50
for s, sx in (("L", 0.22), ("R", -0.22)):
    for f in (1, 780):
        foot_at(RM, HM, s, f, Vector((sx, FOOT_Y, 0.052 + HM.ankle[s].z)), yaw=(-8 if s == "R" else 8))
        knee_pole(RM, s, f, Vector((sx * 1.6, FOOT_Y - 0.9, 0.6)))
ROOT_Z = [(1, 0.70), (50, 0.66), (90, 0.67), (230, 0.80), (300, 0.82), (560, 0.84), (780, 0.84)]
ROOT_FLEX = [(1, 34), (50, 38), (90, 36), (230, 22), (300, 20), (560, 19), (780, 19)]
for f in range(1, 781, 10):
    z = interp(ROOT_Z, f) + (0.006 * math.sin(f * 0.13) if f > 230 else 0)
    HM.key_root(f, Vector((0, FOOT_Y + 0.12, z)), flex=interp(ROOT_FLEX, f))
    # head: up and forward when straining; breaths
    hx = interp([(1, -10), (50, -20), (230, -28), (420, -22), (560, -30), (780, -24)], f)
    HM.key_spine(f, flex=interp([(1, 20), (50, 24), (230, 10), (780, 8)], f) + 1.5 * math.sin(f * 0.06), head=(hx, interp([(1, 0), (320, 0), (360, 24), (420, 24), (470, 0), (540, -14), (600, -14), (780, -14)], f)))
for f in range(1, 781, 4):
    for s, sx in (("L", 0.27), ("R", -0.27)):
        zu = ray_up(sx, HY, f) or 0.4
        place_hand(rigM, s, f, Vector((sx, HY, zu - 0.004)), Vector((0, -0.3, 1)), Vector((0, -1, 0.1)), skin=0.03)
        if f == 1:
            pole(RM, s, 1, Vector((sx * 3.0, FOOT_Y + 0.4, 0.55)))
for s in "LR":
    apply_pose(rigM, s, "shield", 1); apply_pose(rigM, s, "shield", 780)

# Son: lying on his back under the rear overhang, head out near the left edge (face visible), arms beside him
SON_Y = REAR - 0.55
HEADX = -1.58
hip_x = HEADX + 0.62
for f in range(1, 781, 20):
    lying_root(HS, f, Vector((hip_x, SON_Y, 0.13)), roll=interp([(1, 0), (300, 0), (420, 6), (780, 4)], f))
    HS.key_spine(f, flex=-2 + 1.2 * math.sin(f * 0.05), head=(interp([(1, -5), (250, -5), (300, -18), (780, -18)], f), interp([(1, 0), (250, 0), (330, 35), (460, 50), (520, 55), (560, 42), (600, 50), (780, 40)], f)))
for s, sy in (("L", -0.12), ("R", 0.12)):
    for f in (1, 780):
        a_ = HS.ankle[s]
        Wf = Vector((hip_x + 0.84, SON_Y + sy, 0.105))
        M = Matrix.Translation(Wf) @ Matrix.Rotation(R_(90), 4, 'Z') @ Matrix.Rotation(R_(-90 + 55), 4, "X") @ Matrix.Translation(-a_) @ RS.rest("IK_foot." + s)
        RS.key_world("IK_foot." + s, f, M)
        knee_pole(RS, s, f, Vector((hip_x + 0.45, SON_Y + sy * 2, 0.6)))
for f in (1, 780):
    for s, sy in (("L", -0.50), ("R", 0.50)):
        place_hand(rigS, s, f, Vector((hip_x - 0.32, SON_Y + sy, 0.05)), Vector((0, 0, -1)), Vector((0.5, 1.0 if s == "R" else -1.0, 0)), skin=0.012)
        pole(RS, s, f, Vector((hip_x - 0.45, SON_Y + sy * 0.9, 0.6)))
        apply_pose(rigS, s, "relaxed", f)

# ---- cameras B1 / B2a (car rear at +Y, Mom at y≈REAR+0.5)
MOMF = Vector((0, REAR + 0.40, 1.15))
cam_shot("Cam1a", 1, 110, [(1, (1.2, REAR + 1.9, 6.2), (0, REAR - 0.5, 0.4)), (110, (0.9, REAR + 1.6, 5.4), (0, REAR - 0.5, 0.4))], lens=24)
cam_shot("Cam1b", 111, 260, [(111, (-5.0, REAR - 0.3, 1.05), (0, REAR - 0.6, 0.55)), (260, (-4.4, REAR + 0.2, 0.95), (0, REAR - 0.4, 0.6))], lens=26)
cam_shot("Cam1c", 261, 380, [(261, (-2.9, REAR + 2.0, 0.62), (-0.3, REAR - 0.3, 0.62)), (380, (-2.6, REAR + 1.7, 0.58), (-0.3, REAR - 0.3, 0.64))], lens=24)
c1d = cam_shot("Cam1d", 381, 470, [(381, (0.60, REAR - 1.05, 1.36), MOMF + Vector((0, 0.05, 0.02))), (470, (0.30, REAR - 0.92, 1.34), MOMF + Vector((0, 0, 0.04)))], lens=40)
c1e = cam_shot("Cam1e", 471, 600, [(471, (HEADX - 0.25, SON_Y + 1.05, 0.40), (HEADX + 0.15, SON_Y, 0.24)), (600, (HEADX - 0.10, SON_Y + 0.85, 0.36), (HEADX + 0.15, SON_Y, 0.25))], lens=30)
c2a = cam_shot("Cam2a", 601, 780, [(601, (-2.0, REAR + 1.3, 1.2), (0, REAR + 0.45, 0.95)), (780, (-1.7, REAR - 0.1, 1.05), (0, REAR + 0.4, 0.95))], lens=32)
for c in (c1d, c2a): catchlight(rigM, c, 0, 0)
catchlight(rigS, c1e, 0, 0)

# ================================================================== B2b/c: adrenal glands release adrenaline (781..1200), anatomy set at z+100
def dot_stream(proto, name, n, f0, f1, src_fn, vel_fn, life=90, scl=1.0):
    """n copies of proto; each is born at a staggered frame, moves along src + vel*t (keyed), scales in/out; no Scene Time"""
    out = []
    for i in range(n):
        o = proto.copy(); o.name = "%s%03d" % (name, i); proto.users_collection[0].objects.link(o)
        fb = f0 + int((f1 - f0 - 10) * i / n) + random.randint(0, 8); p0 = src_fn(i); v = vel_fn(i)
        for k, f in enumerate((fb - 1, fb, fb + 8, fb + life - 10, fb + life)):
            t = (f - fb) / 60.0
            o.location = p0 + v * max(0, t); o.scale = (0 if k in (0, 4) else (0.4 if k == 1 else 1.0)) * scl * Vector((1, 1, 1))
            o.keyframe_insert("location", frame=f); o.keyframe_insert("scale", frame=f)
        set_interp(o, 'LINEAR')
        out.append(o)
    return out
adr = [bpy.data.objects["Adrenal0"], bpy.data.objects["Adrenal1"]]
for g in adr:
    em = g.active_material
    for f, e in ((781, 0.0), (840, 0.0), (870, 1.0), (940, 0.5), (990, 1.0), (1060, 0.6), (1120, 1.0), (1200, 0.7)):
        P_ = em.node_tree.nodes["Principled BSDF"]
        P_.inputs["Emission Color"].default_value = (1.0, 0.7, 0.1, 1); P_.inputs["Emission Strength"].default_value = e * 1.5
        P_.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
    for f, s_ in ((781, 1.0), (860, 1.0), (880, 1.08), (900, 1.0), (980, 1.08), (1000, 1.0), (1100, 1.08), (1120, 1.0)):
        g.scale = Vector((1.0, 0.55, 0.55)) * s_; g.keyframe_insert("scale", frame=f)
proto = bpy.data.objects["Adr_Proto"]
for gi, g in enumerate(adr):
    c0 = g.location.copy()
    dot_stream(proto, "Adr%d_" % gi, 70, 850, 1200,
               lambda i, c0=c0: c0 + Vector((random.uniform(-0.08, 0.08), random.uniform(-0.04, 0.04), 0.03)),
               lambda i, gi=gi: Vector(((-1 if gi == 0 else 1) * random.uniform(-0.05, 0.12), random.uniform(-0.25, -0.05), random.uniform(0.18, 0.35))), life=110)
K0 = Vector(sc["kid_min"]) + Vector((0, 0, 100)); K1 = Vector(sc["kid_max"]) + Vector((0, 0, 100)); KC = (K0 + K1) / 2
cam_shot("Cam2b", 781, 1000, [(781, (KC.x + 0.25, KC.y - 2.3, KC.z + 0.25), KC + Vector((0, 0, 0.05))), (1000, (KC.x + 0.1, KC.y - 1.55, KC.z + 0.2), KC + Vector((0, 0, 0.1)))], lens=40)
G1 = adr[1].location
cam_shot("Cam2c", 1001, 1200, [(1001, (G1.x + 0.35, G1.y - 0.85, G1.z + 0.12), G1 + Vector((0, 0, 0.1))), (1200, (G1.x - 0.15, G1.y - 0.75, G1.z + 0.2), G1 + Vector((0, 0, 0.16)))], lens=40, fstop=11)

# ================================================================== B3a: blood flow in cut-open arteries (1201..1440)
VY = -22.0; VZ = 100.0
paths = {"Trunk": [(40, 7.2, 0.10), (40, 8.4, 0.10), (40, 9.6, 0.10), (40, 10.6, 0.10)],
         "BrA": [(40, 10.6, 0.10), (39.7, 11.2, 0.10), (39.3, 11.9, 0.10), (38.9, 12.8, 0.10)],
         "BrB": [(40, 10.6, 0.10), (40.3, 11.2, 0.10), (40.7, 11.9, 0.10), (41.1, 12.8, 0.10)]}
def along(pts, u):
    pts = [Vector(p) + Vector((0, VY, VZ)) for p in pts]; seg = [(b - a).length for a, b in zip(pts, pts[1:])]; L = sum(seg); d = u * L
    for a, b, l in zip(pts, pts[1:], seg):
        if d <= l: return a.lerp(b, d / l)
        d -= l
    return pts[-1]
rbc = bpy.data.objects["RBC_Proto"]; o2p = bpy.data.objects["O2_Proto"]
for i in range(110):
    br = "BrA" if i % 2 else "BrB"; full = paths["Trunk"] + paths[br][1:]
    is_o2 = (i % 4 == 0); src = o2p if is_o2 else rbc
    o = src.copy(); o.name = ("FlowO2_%03d" if is_o2 else "FlowRBC_%03d") % i; src.users_collection[0].objects.link(o)
    off = Vector((random.uniform(-0.07, 0.07), random.uniform(-0.04, 0.04), random.uniform(-0.05, 0.02)))
    u0 = random.uniform(-0.6, 0.9); speed = random.uniform(0.0019, 0.0026)   # path fraction per frame
    rot0 = Euler((random.uniform(0, 3), random.uniform(0, 3), random.uniform(0, 3)))
    for f in range(1201, 1441, 12):
        u = u0 + speed * (f - 1201)
        if u < 0 or u > 1: o.scale = (0, 0, 0); o.location = along(full, min(max(u, 0), 1)) + off
        else: o.scale = (0.85, 0.85, 0.85) if not is_o2 else (1, 1, 1); o.location = along(full, u) + off
        o.rotation_euler = (rot0.x + 0.02 * (f - 1201), rot0.y, rot0.z + 0.015 * (f - 1201))
        o.keyframe_insert("location", frame=f); o.keyframe_insert("scale", frame=f); o.keyframe_insert("rotation_euler", frame=f)
    set_interp(o, 'LINEAR')
VC = Vector((40, 10.6 + VY, 0.10 + VZ))
cam_shot("Cam3a", 1201, 1440, [(1201, (40.0, VC.y - 2.6, VC.z + 1.7), VC + Vector((0, -0.6, 0))), (1440, (40.0, VC.y - 1.0, VC.z + 1.25), VC + Vector((0, 0.7, 0)))], lens=30, fstop=11)

# ================================================================== B3b: muscle fills with oxygen/energy and contracts (1441..1680)
mus = bpy.data.objects["Muscle"]; MC = mus.location.copy()
for f in range(1441, 1681, 20):
    k = 0.5 + 0.5 * math.sin((f - 1441) / 240 * 2 * math.pi * 1.5 - math.pi / 2)
    mus.scale = (1 + 0.14 * k, 1 + 0.14 * k, 1 - 0.10 * k); mus.keyframe_insert("scale", frame=f)
dot_stream(o2p, "MusO2_", 90, 1441, 1680, lambda i: MC + Vector((random.choice((-1, 1)) * random.uniform(0.6, 0.9), random.uniform(-0.5, 0.3), random.uniform(-0.6, 0.6))),
           lambda i: Vector((0, 0, 0)), life=70)
for o in [o for o in bpy.data.objects if o.name.startswith("MusO2_")]:
    # drift toward the muscle axis: re-key the end position
    ad_ = o.animation_data.action
    fcs = [fc for fc in _fcurves(ad_) if fc.data_path == "location"]
    for fc in fcs:
        kp = fc.keyframe_points
        if len(kp) >= 5:
            target = (MC.x, MC.y, None)[fc.array_index]
            if target is not None:
                for j in (3, 4): kp[j].co.y = kp[1].co.y + (target - kp[1].co.y) * (0.75 if j == 3 else 0.85)
cam_shot("Cam3b", 1441, 1680, [(1441, (MC.x + 1.6, MC.y - 2.4, MC.z + 0.5), MC), (1680, (MC.x - 0.9, MC.y - 2.5, MC.z + 0.3), MC + Vector((0, 0, 0.05)))], lens=35, fstop=11)

# ================================================================== B4: park, a man heaves a fallen trunk up (1681..2200)
FLOORS[:] = [bpy.data.objects["ParkLawn"]]
lp = bpy.data.objects["LogPivot"]; logo_ = bpy.data.objects["Log"]
# the log's thick end at x≈78.4; he stands at its end facing +X, lifts it from the ground to chest height, then lets it drop aside
LANG = [(1681, 0.0), (1760, 0.0), (1800, -2.0), (1845, -6.5), (1880, -14.0), (1980, -16.0), (2040, -15.5), (2060, -15.5), (2085, 0.0), (2200, 0.0)]
for f in range(1681, 2241, 3):
    a = interp(LANG, f) if f <= 2060 else (-15.5 * max(0.0, 1 - ((f - 2060) / 25.0) ** 2) if f < 2085 else (1.2 * math.exp(-(f - 2085) / 6.0) * math.sin((f - 2085) * 0.6)))
    lp.rotation_euler.y = R_(-a); lp.keyframe_insert("rotation_euler", index=1, frame=f)   # thick end (-X) rises
bpy.context.view_layer.update()
XG = 79.1; MY = -0.50; XL = XG     # he stands beside the trunk (log axis along X at y=0), facing it (+Y), near the thick end
def log_frame(f, dx, a_deg):
    """point on the log surface dx in from the thick end at angle a (0 = bottom, + toward his side -Y), with normal and wrap tangent"""
    sc.frame_set(f); bpy.context.view_layer.update()
    M = logo_.matrix_world; M3 = M.to_3x3().normalized(); r_ = 0.17 * (1.15 - 0.10 * dx)
    a_ = R_(a_deg); n_l = Vector((0, -math.sin(a_), -math.cos(a_))); t_l = Vector((0, math.cos(a_), -math.sin(a_)))
    # exact surface point + normal: ray from the axis outward in the log's local space
    hit, loc, nrm_l, idx = logo_.ray_cast(Vector((-1.6 + dx, 0, 0)), n_l)
    if not hit: loc, nrm_l = Vector((-1.6 + dx, 0, 0)) + n_l * r_, n_l
    nW = (M.to_3x3().inverted().transposed() @ nrm_l).normalized()
    tW = (M3 @ t_l); tW = (tW - nW * tW.dot(nW)).normalized()
    return M @ loc, nW, tW
for f in (1681, 2240):
    for s, sx in (("L", -0.24), ("R", 0.24)):
        foot_at(RX, HX, s, f, Vector((XG + sx * 1.25, MY - 0.06, 0.0 + HX.ankle[s].z)), yaw=180 + (-8 if s == "L" else 8))
        knee_pole(RX, s, f, Vector((XG + sx * 3.0, MY + 0.5, 0.6)))
RZS = HX.root_head.z - 0.025; print('MAN_ROOT', HX.root_head.z)
RZ = [(1681, RZS), (1740, RZS), (1775, 0.50), (1805, 0.49), (1825, 0.51), (1850, 0.58), (1865, 0.63), (1880, 0.80), (1980, 0.82), (2060, 0.82), (2090, RZS), (2200, RZS)]
RF = [(1681, 2), (1740, 4), (1775, 44), (1805, 44), (1840, 30), (1880, 14), (1980, 8), (2060, 8), (2090, 2), (2200, 0)]
for f in range(1681, 2241, 8):
    HX.key_root(f, Vector((XG, MY - 0.10, interp(RZ, f))), yaw=180, flex=interp(RF, f))
    HX.key_spine(f, flex=interp([(1681, 0), (1740, 2), (1775, 22), (1880, 6), (2060, 4), (2100, -4), (2200, -6)], f) + 1.2 * math.sin(f * 0.07),
                 head=(interp([(1681, 0), (1740, 10), (1775, -10), (1880, -14), (2060, -6), (2100, -12), (2200, -10)], f), 0))
for f in list(range(1780, 2061, 4)):
    for s, dx in (("L", XG - 0.28 - 78.4), ("R", XG + 0.28 - 78.4)):
        pnt, nrm, tan = log_frame(f, dx, 65)
        place_hand(rigX, s, f, pnt, -nrm, tan, skin=((0.17 if 1836 <= f <= 1880 else 0.11) if s == "L" else 0.06))
for s, sx in (("L", -1), ("R", 1)):
    # before the grip: arms hang relaxed, then reach down to the trunk
    place_hand(rigX, s, 1681, Vector((XG + sx * 0.26, MY - 0.05, 0.80)), Vector((-sx, 0, 0)), Vector((0, 0, -1)), skin=0.0)
    place_hand(rigX, s, 1722, Vector((XG + sx * 0.30, MY + 0.30, 0.86)), Vector((-sx * 0.5, 0.3, -1)), Vector((0, 0.6, -0.8)), skin=0.0)
    pnt0, nrm0, tan0 = log_frame(1755, (XG + sx * 0.28 - 78.4), 65)
    place_hand(rigX, s, 1755, pnt0 + nrm0 * 0.22, -nrm0, tan0, skin=0.03)
    # release, then both arms up in triumph (hands above the head, palms forward, elbows bent)
    pnt1, nrm1, tan1 = log_frame(2060, (XG + sx * 0.28 - 78.4), 65)
    place_hand(rigX, s, 2066, pnt1 + nrm1 * 0.20, -nrm1, tan1, skin=0.05)
    place_hand(rigX, s, 2080, Vector((XG + sx * 0.32, MY - 0.02, 1.05)), Vector((0, 1, 0)), Vector((0, 0.2, 1)), skin=0.0)
    place_hand(rigX, s, 2120, Vector((XG + sx * 0.55, MY - 0.02, 1.95)), Vector((0, 1, 0)), Vector((sx * 0.3, 0, 1)), skin=0.0)
    place_hand(rigX, s, 2200, Vector((XG + sx * 0.58, MY - 0.02, 2.00)), Vector((0, 1, 0)), Vector((sx * 0.3, 0, 1)), skin=0.0)
    place_hand(rigX, s, 2240, Vector((XG + sx * 0.64, MY - 0.02, 1.96)), Vector((0, 1, 0)), Vector((sx * 0.4, 0, 1)), skin=0.0)
    pole(RX, s, 2240, Vector((XG + sx * 0.8, MY - 0.4, 1.3))); apply_pose(rigX, s, "open_alarm", 2240, amount=0.6)
    pole(RX, s, 1681, Vector((XG + sx * 0.6, MY - 0.6, 0.9))); pole(RX, s, 2060, Vector((XG + sx * 0.7, MY - 0.5, 0.7)))
    pole(RX, s, 2120, Vector((XG + sx * 0.8, MY - 0.4, 1.3))); pole(RX, s, 2200, Vector((XG + sx * 0.8, MY - 0.4, 1.3)))
    apply_pose(rigX, s, "relaxed", 1681); apply_pose(rigX, s, "relaxed", 1755)
    apply_pose(rigX, s, "relaxed", 1780); apply_pose(rigX, s, "relaxed", 2060)
    apply_pose(rigX, s, "open_alarm", 2080, amount=0.6); apply_pose(rigX, s, "open_alarm", 2200, amount=0.6)
# DA KRAS FILMS logo on his yellow T-shirt chest (projected from an empty on the chest bone, front half only)
tee = next(o for o in rigX.children if "male_casualsuit04" in o.name)
emp = bpy.data.objects.new("LogoProj", None); sc.collection.objects.link(emp); emp.parent = rigX; emp.parent_type = 'BONE'; emp.parent_bone = "spine02"
sc.frame_set(1681); bpy.context.view_layer.update()
cb = rigX.matrix_world @ rigX.pose.bones["spine02"].head
emp.matrix_world = Matrix.Translation(cb) @ Matrix.Rotation(R_(90), 4, 'Z')
for m in tee.data.materials:
    if not m: continue
    nt = m.node_tree
    tcn = nt.nodes.new("ShaderNodeTexCoord"); tcn.object = emp
    mixn = nt.nodes["Principled BSDF"].inputs["Base Color"].links[0].from_node
    mp = nt.nodes.new("ShaderNodeMapping"); nt.links.new(tcn.outputs["Object"], mp.inputs[0])
    # object space of the empty: X right->left of chest, Z up, Y forward; logo 0.26 m wide, 967x414
    mp.vector_type = 'POINT'
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tcn.outputs["Object"], sep.inputs[0])
    cmb = nt.nodes.new("ShaderNodeCombineXYZ")
    u = nt.nodes.new("ShaderNodeMath"); u.operation = 'MULTIPLY_ADD'; u.inputs[1].default_value = 1 / 0.26; u.inputs[2].default_value = 0.5
    v = nt.nodes.new("ShaderNodeMath"); v.operation = 'MULTIPLY_ADD'; v.inputs[1].default_value = 1 / (0.26 * 414 / 967); v.inputs[2].default_value = 0.5 - 0.17 / (0.26 * 414 / 967)
    nt.links.new(sep.outputs["Y"], u.inputs[0]); nt.links.new(sep.outputs["Z"], v.inputs[0])
    nt.links.new(u.outputs[0], cmb.inputs["X"]); nt.links.new(v.outputs[0], cmb.inputs["Y"])
    ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = bpy.data.images.load(BRAND + "DaKrasFilms_logo_dark.png"); ti.extension = 'CLIP'
    nt.links.new(cmb.outputs[0], ti.inputs[0])
    front = nt.nodes.new("ShaderNodeMath"); front.operation = 'GREATER_THAN'; front.inputs[1].default_value = 0.0; nt.links.new(sep.outputs["X"], front.inputs[0])
    am = nt.nodes.new("ShaderNodeMath"); am.operation = 'MULTIPLY'; nt.links.new(ti.outputs["Alpha"], am.inputs[0]); nt.links.new(front.outputs[0], am.inputs[1])
    mxl = nt.nodes.new("ShaderNodeMix"); mxl.data_type = 'RGBA'
    outs = list(mixn.outputs['Result'].links)
    nt.links.new(am.outputs[0], mxl.inputs['Factor']); nt.links.new(mixn.outputs['Result'], mxl.inputs['A']); nt.links.new(ti.outputs["Color"], mxl.inputs['B'])
    for lk in outs: nt.links.new(mxl.outputs['Result'], lk.to_socket)
c4a = cam_shot("Cam4a", 1681, 1880, [(1681, (XG + 2.2, 3.0, 1.3), (XG, -0.4, 0.7)), (1880, (XG + 1.9, 2.6, 1.2), (XG, -0.4, 0.75))], lens=28)
c4b = cam_shot("Cam4b", 1881, 2060, [(1881, (XG + 0.75, 2.0, 1.25), (XG, MY, 1.1)), (2060, (XG + 0.6, 1.8, 1.25), (XG, MY, 1.12))], lens=35)
c4c = cam_shot("Cam4c", 2061, 2200, [(2061, (XG + 0.35, 2.6, 1.35), (XG, MY, 1.3)), (2200, (XG + 0.25, 2.3, 1.35), (XG, MY, 1.32))], lens=35)
for c in (c4a, c4b, c4c): catchlight(rigX, c, 0, 0)

eye_fix_all()
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("ANIM_OK", OUT)
