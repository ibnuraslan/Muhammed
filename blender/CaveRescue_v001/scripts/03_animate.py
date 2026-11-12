"""CaveRescue blocking animation: characters, props, FX keys, lights and the one continuous camera.
blender -b scene.blend --python 03_animate.py -- <out.blend>
"""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
V = Vector
random.seed(7)
CX, DX, WZ = sc["CX"], sc["DX"], sc["WATER_Z"]
TERR, TUNL, LEDGE = bpy.data.objects["S1_Terrain"], bpy.data.objects["S2_Tunnel"], bpy.data.objects["S4_Ledge"]
TUN_D = [V(p) for p in (lambda o: [])(None)]
# tunnel centreline (dense, from the mesh build): recompute from the stored control points
TUN = [V(p) for p in sc["TUN"]]
def _cr(P, step=0.25):
    out = []
    for i in range(len(P) - 1):
        p0 = P[max(i - 1, 0)]; p1 = P[i]; p2 = P[i + 1]; p3 = P[min(i + 2, len(P) - 1)]
        n_ = max(2, int((p2 - p1).length / step))
        for k in range(n_):
            t = k / n_
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-1]); return out
TC = _cr([V((0, -12, 0.2))] + TUN[1:])
TS = [0.0]
for a, b in zip(TC, TC[1:]): TS.append(TS[-1] + (b - a).to_2d().length)
S_MOUTH = min(range(len(TC)), key=lambda i: abs(TC[i].y + 1.5)); S_MOUTH = TS[S_MOUTH]
def tun_at(s):
    """centreline point + side vector at arc length s (s = 0 at y = -12)"""
    s = max(0.0, min(TS[-1] - 0.01, s))
    i = max(j for j in range(len(TS) - 1) if TS[j] <= s); u = (s - TS[i]) / (TS[i + 1] - TS[i])
    p = TC[i].lerp(TC[i + 1], u); fw = (TC[i + 1] - TC[i]); fw.z = 0; fw.normalize()
    return p, fw, fw.cross(V((0, 0, 1))).normalized()
PAS = [V(p) for p in sc["PAS"]]

def _ray(o, x, y, z0):
    hit, loc, nrm, idx = o.ray_cast(V((x, y, z0)), V((0, 0, -1)))
    return loc.z if hit else None
def ground_z(x, y):
    if x > 300:
        z = _ray(LEDGE, x, y, 3.0); return z if z is not None else -3.0
    if x < -300:
        return 0.0
    if y > -2.6:
        i = min(range(len(TC)), key=lambda k: (TC[k].x - x) ** 2 + (TC[k].y - y) ** 2)
        z = _ray(TUNL, x, y, TC[i].z + 1.6)
        if z is not None: return z
    z = _ray(TERR, x, y, 60.0); return z if z is not None else 0.0

def Rx(d): return Matrix.Rotation(R_(d), 3, 'X')
def Ry(d): return Matrix.Rotation(R_(d), 3, 'Y')
def Rz(d): return Matrix.Rotation(R_(d), 3, 'Z')

# =============================================================== characters
BASE = ["Boy1", "Boy2", "Boy3", "Boy4", "Boy5", "Coach", "DiverA", "DiverB", "DiverC", "Crowd1", "Crowd2", "Crowd3", "Crowd4"]
RIG, HUM = {}, {}
for n in BASE:
    RIG[n] = make_human_ctrl(bpy.data.objects[n]); HUM[n] = Human(RIG[n])
def clone(src, name):
    so = bpy.data.objects[src]; o = so.copy(); o.name = name; sc.collection.objects.link(o)
    o.animation_data_clear()
    for pb in o.pose.bones:
        for c_ in pb.constraints:
            for k in ('target', 'pole_target'):
                if getattr(c_, k, None) == so: setattr(c_, k, o)
    for ch in so.children:
        c2 = ch.copy(); c2.parent = o; sc.collection.objects.link(c2); c2.name = name + "." + ch.name.split(".", 1)[1]
        for m in c2.modifiers:
            if m.type == 'ARMATURE': m.object = o
    RIG[name] = Rig(o); HUM[name] = Human(RIG[name])
HB = ["HB%d" % i for i in range(1, 8)]
for i, n in enumerate(HB):
    clone(["Boy1", "Boy3", "Boy4", "Boy5", "Boy1", "Boy4", "Boy3"][i], n)
CROWD = ["Crowd%d" % i for i in range(1, 5)]
ALL = BASE + HB
PARK = {n: V((250.0, 300.0 + 6 * i, -80.0)) for i, n in enumerate(ALL)}

def body_R(yaw=0.0, flex=0.0, side=0.0):
    return Rz(yaw) @ Rx(flex) @ Ry(side)
def bw(n, P, Rb, local):
    return P + Rb @ (local - HUM[n].root_head)
def rest_head(n, bone): return RIG[n].BN[bone].head_local.copy()

def key_foot_free(n, s, f, W, Rw):
    H = HUM[n]; a = H.ankle[s]
    M = Matrix.Translation(W) @ Rw.to_4x4() @ Matrix.Translation(-a) @ H.r.rest("IK_foot." + s)
    H.r.key_world("IK_foot." + s, f, M)
    pole = W + Rw @ V((0, -0.7, 0.45))
    pb = H.r.PB["Pole_knee." + s]; nm = "Pole_knee." + s
    pb.location = H.r.rest(nm).to_3x3().inverted() @ (pole - H.r.BN[nm].head_local); pb.keyframe_insert("location", frame=f, group=nm)

def relaxed_hand(n, P, Rb, s, fwd=0.0, out=0.0, up=0.0):
    sx = 1 if s == "L" else -1
    sh = rest_head(n, "upperarm01." + s); wr = rest_head(n, "wrist." + s)
    L = (sh - wr).length
    loc = sh + V((sx * (0.07 + out), -fwd, -L * 0.93 + up))
    W = bw(n, P, Rb, loc)
    d = Rb @ V((0, -0.15 * fwd, -1)).normalized(); nn = Rb @ V((-sx, 0, 0))
    return W, d, nn

def elbow_pole(n, P, Rb, s, back=0.55, out=0.25, down=-0.1):
    sx = 1 if s == "L" else -1
    return bw(n, P, Rb, rest_head(n, "lowerarm01." + s) + V((out * sx, back, down)))

def key_hands(n, f, P, Rb, hands):
    """hands: {s: (W, d, n) or None for relaxed} ; poles follow the body"""
    for s in "LR":
        h = hands.get(s) if hands else None
        if h is None: h = relaxed_hand(n, P, Rb, s)
        pole = h[3] if len(h) > 3 else elbow_pole(n, P, Rb, s)
        HUM[n].key_hand(s, f, h[0], h[1], h[2], pole)

def park(n, f):
    P = PARK[n]; H = HUM[n]; Rb = body_R()
    H.key_root(f, P); H.key_spine(f)
    for s in "LR":
        key_foot_free(n, s, f, bw(n, P, Rb, H.ankle[s]), Rb)
    key_hands(n, f, P, Rb, {})

TELE = {n: set() for n in ALL}
exec(open(os.path.join(HERE, "..", "..", "pipeline", "hand_poses.py")).read())     # shared presets: relaxed, wrap_grip, pinch, tripod ...
for _n in RIG: add_hand_limits(RIG[_n].o)
m_strap_h = bpy.data.materials.new("M_Harness"); m_strap_h.use_nodes = True
m_strap_h.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.9, 0.45, 0.05, 1)
def key_elbow(n, s, f, pole_w):
    pb = RIG[n].PB["Pole_elbow." + s]; nm = "Pole_elbow." + s
    pb.location = RIG[n].rest(nm).to_3x3().inverted() @ (pole_w - RIG[n].BN[nm].head_local); pb.keyframe_insert("location", frame=f, group=nm)
def key_fingers(n, s, f, pose):
    """key a shared hand_poses preset; numbers map to the nearest preset (no hand-set finger angles)"""
    if not isinstance(pose, str):
        pose = "flat_palm" if pose <= 10 else "relaxed" if pose <= 25 else "cup_hold" if pose <= 45 else "wrap_grip"
    apply_pose(RIG[n].o, s, pose, f)

# ---------------------------------------------------------------- seated huddle / kneel / swim poses
def seated(n, f, x, y, yaw, lean=22.0, head=(-10.0, 0.0), hug=True, hand_over=None, knee=0.0):
    """sitting on the ledge, knees up, arms around the knees"""
    H = HUM[n]; g = ground_z(x, y)
    P = V((x, y, g + 0.11)); Rb = body_R(yaw, lean * 0.5)
    H.key_root(f, P, yaw=yaw, flex=lean * 0.5)
    H.key_spine(f, flex=lean, head=head)
    fw = Rz(yaw) @ V((0, -1, 0)); sd = Rz(yaw) @ V((1, 0, 0))
    for s in "LR":
        sx = 1 if s == "L" else -1
        xy = (V((x, y, 0)) + fw * (0.36 + knee + (0.08 if n == "Coach" else 0.0)) + sd * (0.12 * sx)).to_2d()
        H.key_foot(s, f, xy, yaw, 0.0, 0.0)
        pb = H.r.PB["Pole_knee." + s]; nm = "Pole_knee." + s
        pole = V((xy.x, xy.y, g + 1.2)) + fw * 0.3
        pb.location = H.r.rest(nm).to_3x3().inverted() @ (pole - H.r.BN[nm].head_local); pb.keyframe_insert("location", frame=f, group=nm)
    hands = {}
    for s in "LR": key_fingers(n, s, f, ("shield" if (hand_over and s in hand_over) else "cup_hold") if hug else "relaxed")
    if hug:
        for s in "LR":
            sx = 1 if s == "L" else -1
            W = V((x, y, g)) + fw * (0.40 + knee) + sd * (0.13 * sx) + V((0, 0, 0.34))
            hands[s] = (W, (-sd * sx + V((0, 0, -0.3))).normalized(), -fw, V((x, y, g + 0.4)) + sd * (0.7 * sx) + fw * 0.1)
    if hug and n == "Coach":      # adult: hands rest on top of each knee, well apart
        for s in "LR":
            sx = 1 if s == "L" else -1
            W = V((x, y, g)) + fw * 0.30 + sd * (0.2 * sx) + V((0, 0, 0.47))
            hands[s] = (W, (fw + V((0, 0, -0.4))).normalized(), V((0, 0, -1)), V((x, y, g + 0.4)) + sd * (0.8 * sx))
    if hand_over:
        hands.update(hand_over)
    key_hands(n, f, P, Rb, hands)
    return P, Rb

def kneel(n, f, x, y, yaw, lean=15.0, head=(-15.0, 0.0), hands=None, sit_back=0.0):
    """kneeling on both knees, sitting a little back toward the heels"""
    H = HUM[n]; g = ground_z(x, y)
    thigh = (rest_head(n, "upperleg01.L") - rest_head(n, "lowerleg01.L")).length
    P = V((x, y, g + thigh * (0.95 - 0.35 * sit_back) + 0.08)); Rb = body_R(yaw, lean * 0.4)
    fw = Rz(yaw) @ V((0, -1, 0)); sd = Rz(yaw) @ V((1, 0, 0))
    H.key_root(f, P + fw * (0.04 - 0.12 * sit_back), yaw=yaw, flex=lean * 0.4)
    H.key_spine(f, flex=lean, head=head)
    shin = (rest_head(n, "lowerleg01.L") - H.ankle["L"]).length
    for s in "LR":
        sx = 1 if s == "L" else -1
        base = V((x, y, 0)) + sd * (0.11 * sx) - fw * (shin * 0.95 - 0.1)
        gz_ = ground_z(base.x, base.y)
        W = V((base.x, base.y, gz_ + 0.07))
        key_foot_free(n, s, f, W, Rz(yaw) @ Rx(-75))
        pb = H.r.PB["Pole_knee." + s]; nm = "Pole_knee." + s
        pole = V((x, y, g + 0.2)) + fw * 1.0 + sd * 0.1 * sx
        pb.location = H.r.rest(nm).to_3x3().inverted() @ (pole - H.r.BN[nm].head_local); pb.keyframe_insert("location", frame=f, group=nm)
    key_hands(n, f, P, Rb, hands or {})
    return P, Rb

def swim(n, f, P, yaw, pitch=0.0, roll=0.0, phase=0.0, kick=1.0, hands=None):
    """horizontal, face down, head toward heading; flutter kick from the hips"""
    H = HUM[n]; Rb = body_R(yaw, 90 + pitch, roll)
    H.key_root(f, P, yaw=yaw, flex=90 + pitch, side=roll)
    H.key_spine(f, flex=-8, head=(-35, 0))
    for s in "LR":
        sx = 1 if s == "L" else -1
        k = kick * 0.12 * math.sin(phase + (0 if s == "L" else math.pi))
        loc = H.ankle[s] + V((-0.02 * sx, 0.06 + k, 0.03))
        key_foot_free(n, s, f, bw(n, P, Rb, loc), Rb @ Rx(-55 + 20 * k / 0.12))
    hh = {}
    for s in "LR":
        if hands and s in hands: hh[s] = hands[s]
        else:
            W, d, nn = relaxed_hand(n, P, Rb, s, fwd=-0.02, out=0.05, up=0.12)
            hh[s] = (W, d, nn)
    key_hands(n, f, P, Rb, hh)
    return Rb

# ---------------------------------------------------------------- props on bones
def attach(o, n, bone, f, M_world):
    """Child Of the bone, holding M_world at frame f"""
    ev(f)
    rig = RIG[n].o
    o.matrix_world = M_world
    c_ = o.constraints.new('CHILD_OF'); c_.target = rig; c_.subtarget = bone
    c_.inverse_matrix = (rig.matrix_world @ rig.pose.bones[bone].matrix).inverted()
    return c_
m_lamp = bpy.data.materials.new("M_TorchBody"); m_lamp.use_nodes = True
m_lamp.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.05, 0.05, 0.05, 1)
m_lens = bpy.data.materials.new("M_TorchLens"); m_lens.use_nodes = True
_ln = m_lens.node_tree.nodes["Principled BSDF"]; _ln.inputs['Emission Color'].default_value = (1, 0.92, 0.75, 1); _ln.inputs['Emission Strength'].default_value = 25
m_band = bpy.data.materials.new("M_Headband"); m_band.use_nodes = True
m_band.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.03, 0.03, 0.035, 1)
def head_frame(n):
    """world matrix of the head at rest (character at origin), forehead point + forward"""
    hb = RIG[n].BN["head"]
    top = hb.tail_local; base = hb.head_local
    return base, top
TORCH = {}
def head_torch(n, energy=60.0, f_on=1):
    """lamp on an elastic band at the forehead; spot light aimed forward; Child Of head (rest-pose attach at frame 0 park)"""
    rig = RIG[n].o; hb = RIG[n].BN["head"]
    # forehead in rest pose: in front of the head bone, 70% up
    base, top = hb.head_local, hb.tail_local
    up = (top - base).normalized(); fwd = V((0, -1, 0))
    body = bpy.data.objects[n + ".body"]
    # find the forehead surface by casting from the front
    o_ = base.lerp(top, 0.55) + fwd * 0.5
    hit, loc, nrm, idx = body.ray_cast(o_, -fwd, depsgraph=bpy.context.evaluated_depsgraph_get())
    fh = loc if hit else base.lerp(top, 0.55) + fwd * 0.1
    bpy.ops.mesh.primitive_cylinder_add(radius=0.022, depth=0.03, location=fh + fwd * 0.024, rotation=(R_(90), 0, 0))
    lamp = bpy.context.active_object; lamp.name = n + "_HeadTorch"; lamp.data.materials.append(m_lamp)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.016, depth=0.004, location=fh + fwd * 0.04, rotation=(R_(90), 0, 0))
    lens = bpy.context.active_object; lens.name = n + "_TorchLens"; lens.data.materials.append(m_lens); lens.parent = lamp
    lens.matrix_parent_inverse = lamp.matrix_world.inverted()
    # band: a thin torus around the head at forehead height
    hc = base.lerp(top, 0.55)
    r = (fh - V((hc.x, hc.y, fh.z))).length + 0.006
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.006, location=(hc.x, hc.y + 0.01, fh.z), rotation=(R_(-8), 0, 0))
    band = bpy.context.active_object; bpy.data.objects.remove(band, do_unlink=True)
    sp = bpy.data.objects.new(n + "_TorchLight", bpy.data.lights.new(n + "_TorchLight", 'SPOT'))
    sp.data.energy = energy; sp.data.spot_size = R_(55); sp.data.spot_blend = 0.6; sp.data.shadow_soft_size = 0.02
    sp.data.color = (1.0, 0.93, 0.8); sc.collection.objects.link(sp)
    sp.location = fh + fwd * 0.05; sp.rotation_euler = (R_(-90), 0, 0)    # spot points -Z local -> rotate to -Y
    sp.parent = lamp; sp.matrix_parent_inverse = lamp.matrix_world.inverted()
    # Child Of head at rest pose: evaluate the rig at rest (pose cleared) by computing from rest matrices
    c_ = lamp.constraints.new('CHILD_OF'); c_.target = rig; c_.subtarget = "head"
    c_.inverse_matrix = (hb.matrix_local).inverted()
    TORCH[n] = sp
    return lamp, sp
# diver gear: tank on the back (spine03), black full mask (head)
m_tank = bpy.data.materials.get("M_Tank"); m_tank.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.32, 0.3, 0.22, 1); m_mask = bpy.data.materials.new("M_DiveMask"); m_mask.use_nodes = True
_mp = m_mask.node_tree.nodes["Principled BSDF"]; _mp.inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1); _mp.inputs['Roughness'].default_value = 0.35
m_visor = bpy.data.materials.new("M_Visor"); m_visor.use_nodes = True
_vp = m_visor.node_tree.nodes["Principled BSDF"]; _vp.inputs['Base Color'].default_value = (0.6, 0.7, 0.75, 1); _vp.inputs['Roughness'].default_value = 0.02
_vp.inputs['Transmission Weight'].default_value = 0.9
def rest_attach(o, n, bone):
    c_ = o.constraints.new('CHILD_OF'); c_.target = RIG[n].o; c_.subtarget = bone
    c_.inverse_matrix = RIG[n].BN[bone].matrix_local.inverted(); return c_
def diver_gear(n):
    sp3 = RIG[n].BN["spine03"]; body = bpy.data.objects[n + ".body"]
    c0 = sp3.head_local
    hit, loc, nrm, idx = body.ray_cast(c0 + V((0, 0.5, 0)), V((0, -1, 0)), depsgraph=bpy.context.evaluated_depsgraph_get())
    back = loc if hit else c0 + V((0, 0.13, 0))
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.085, depth=0.62, location=back + V((0.1 * sx, 0.1, -0.05)))
        t = bpy.context.active_object; t.name = "%s_Tank%d" % (n, sx); t.data.materials.append(m_tank)
        rest_attach(t, n, "spine03")
    # mask: dark rubber oval + glass plate over the eyes/nose, slightly larger than the face (no clipping)
    hb = RIG[n].BN["head"]; hc = hb.head_local.lerp(hb.tail_local, 0.35)
    hit, loc, nrm, idx = body.ray_cast(hc + V((0, -0.5, 0)), V((0, 1, 0)), depsgraph=bpy.context.evaluated_depsgraph_get())
    face = loc if hit else hc + V((0, -0.1, 0))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=24, ring_count=12, location=face + V((0, -0.032, 0.005)))
    mk = bpy.context.active_object; mk.name = n + "_Mask"; mk.scale = (0.075, 0.018, 0.06); mk.data.materials.append(m_mask)
    rest_attach(mk, n, "head")
    return mk
for n in ("DiverA", "DiverB", "DiverC"):
    diver_gear(n)
for n in ["Boy1", "Boy2", "Boy3", "Boy4", "Boy5", "Coach"] + HB:
    head_torch(n, 70.0)
for n in ("DiverA", "DiverB", "DiverC"):
    head_torch(n, 70.0)
# head torches off for the crowd clones (they are not cloned with lamps)

# =============================================================== BEAT 1-2: walk in, flood, run deeper (frames 1-590)
WALK = [("Coach", 0.1, -1.4), ("Boy1", -0.7, -2.8), ("Boy2", 0.7, -3.1), ("Boy3", -0.7, -4.5), ("Boy4", 0.75, -4.8), ("Boy5", 0.0, -6.1)]
F_END_RUN = 590
def s_of(f, s_start):
    # 1.3 m/s walking, accelerating to 2.6 m/s running from f 300 (beat 2)
    t = (f - 1) / 60.0
    s = s_start + 1.3 * t
    if f > 300:
        tr = (f - 300) / 60.0
        s += 1.3 * (tr - (1 - math.exp(-tr * 2.5)) / 2.5)
    return s
for n, lane, s0 in WALK:
    S0 = S_MOUTH + s0 - 4.5
    def path(f, S0=S0, lane=lane):
        p, fw, sd = tun_at(s_of(f, S0)); q = p + sd * lane * (1 + 0.1 * math.sin(f * 0.01))
        return V((q.x, q.y, 0))
    def yaw_fn(f, S0=S0):
        p, fw, sd = tun_at(s_of(f, S0)); return math.degrees(math.atan2(fw.x, -fw.y)) + 180 - 180
    H = HUM[n]
    # walk (1-300) then run (300-590): stride grows with speed
    H.walk(path, lambda f, S0=S0: math.degrees(math.atan2(tun_at(s_of(f, S0))[1].x, -tun_at(s_of(f, S0))[1].y)), 1, 300, stride=0.62 if n != "Coach" else 0.75,
           lift=0.08, lean=5, step=2)
    H.walk(path, lambda f, S0=S0: math.degrees(math.atan2(tun_at(s_of(f, S0))[1].x, -tun_at(s_of(f, S0))[1].y)), 302, F_END_RUN, stride=1.15 if n != "Coach" else 1.35,
           duty=0.42, lift=0.14, bob=0.04, crouch=0.06, lean=16, step=2)
    # arms: swing while walking, pump while running; torch beams swing with the head
    for f in range(1, F_END_RUN + 1, 4):
        p = path(f); yw = math.degrees(math.atan2(tun_at(s_of(f, S0))[1].x, -tun_at(s_of(f, S0))[1].y))
        P = V((p.x, p.y, ground_z(p.x, p.y) + H.root_head.z)); Rb = body_R(yw, 6 if f < 300 else 14)
        run = f > 300; ph = s_of(f, S0) / ((0.62 if f < 300 else 1.15) * 1.0) * 2 * math.pi
        hh = {}
        for s in "LR":
            sw = math.sin(ph + (0 if s == "L" else math.pi))
            W, d, nn = relaxed_hand(n, P, Rb, s, fwd=(0.18 if not run else 0.28) * sw + (0.1 if run else 0.0), up=0.18 if run else 0.0, out=0.06 if run else 0.0)
            hh[s] = (W, d, nn, elbow_pole(n, P, Rb, s, out=0.08 if run else 0.18))
        key_hands(n, f, P, Rb, hh)
        if run:
            H.key_spine(f, flex=16, twist=-8 * math.sin(ph), head=(8 * math.sin(f * 0.11), 25 * math.sin(f * 0.045) if n in ("Boy3", "Boy5") else 10 * math.sin(f * 0.07)))
    TELE[n].add(F_END_RUN)

# flood strip along the tunnel floor with a moving front (transparent beyond FrontY), surge froth at the front
bm = bmesh.new(); rows = []
for i in range(0, len(TC), 2):
    p, fw, sd = tun_at(TS[i]); r_ = []
    for k in range(-6, 7):
        q = p + sd * (k * 0.42); r_.append(bm.verts.new((q.x, q.y, p.z + 0.05)))
    rows.append(r_)
for a, b in zip(rows, rows[1:]):
    for k in range(12): bm.faces.new((a[k], a[k + 1], b[k + 1], b[k]))
fm = bpy.data.meshes.new("S2_FloodStrip"); bm.to_mesh(fm); bm.free()
flood = bpy.data.objects.new("S2_FloodStrip", fm); bpy.data.collections["S2_Tunnel"].objects.link(flood)
for pg in fm.polygons: pg.use_smooth = True
md = flood.modifiers.new("Sub", 'SUBSURF'); md.subdivision_type = 'SIMPLE'; md.levels = md.render_levels = 2
dsp = flood.modifiers.new("Wave", 'DISPLACE'); dsp.texture = bpy.data.textures["FloodWave"]; dsp.strength = 0.08
mf = bpy.data.materials["M_FloodWater"].copy(); mf.name = "M_FloodStrip"
fn_, fl_ = mf.node_tree.nodes, mf.node_tree.links
out = next(x for x in fn_ if x.type == 'OUTPUT_MATERIAL'); src = out.inputs['Surface'].links[0].from_socket
tcd = fn_.new('ShaderNodeTexCoord'); sxyz = fn_.new('ShaderNodeSeparateXYZ'); fy = fn_.new('ShaderNodeValue'); fy.name = "FrontY"
cmp = fn_.new('ShaderNodeMath'); cmp.operation = 'GREATER_THAN'; tr = fn_.new('ShaderNodeBsdfTransparent'); mx = fn_.new('ShaderNodeMixShader')
fl_.new(tcd.outputs['Object'], sxyz.inputs['Vector']); fl_.new(sxyz.outputs['Y'], cmp.inputs[0]); fl_.new(fy.outputs[0], cmp.inputs[1])
fl_.new(cmp.outputs[0], mx.inputs['Fac']); fl_.new(src, mx.inputs[1]); fl_.new(tr.outputs[0], mx.inputs[2]); fl_.new(mx.outputs[0], out.inputs['Surface'])
flood.data.materials.append(mf)
surge = bpy.data.objects["S2_SurgeFront"]
bpy.data.objects["S2_FloodWater"].hide_render = True
last_boy_S0 = S_MOUTH - 6.1 - 4.5
for f in list(range(1, 600, 6)) + [600, 606]:
    if f < 330: front_s = -10.0; depth = -0.3
    else:
        front_s = min(s_of(f, last_boy_S0) - 2.2 - 1.5 * math.exp(-(f - 330) / 40), TS[-1]); depth = min(0.28, -0.3 + (f - 330) / 120 * 0.58)
    p, fw, sd = tun_at(max(front_s, 0.0))
    fy.outputs[0].default_value = p.y if front_s > 0 else -50.0; fy.outputs[0].keyframe_insert("default_value", frame=f)
    flood.location.z = depth if f < 600 else -6.0; flood.keyframe_insert("location", frame=f)
    surge.location = p + V((0, 0, 0.1 + max(depth, 0) * 0.6)) if front_s > 0 else V((0, -60, -20))
    surge.rotation_euler = (0, 0, math.atan2(-fw.x, fw.y)); surge.scale = (2.3, 0.9 + 0.3 * math.sin(f * 0.3), 0.45)
    for k in ("location", "rotation_euler", "scale"): surge.keyframe_insert(k, frame=f)
# rain + torrent at the mouth (beat 2), sky darkens
rain_v = bpy.data.materials["M_Rain"].node_tree.nodes["RainAmount"].outputs[0]
for f, v in ((1, 0.0), (285, 0.0), (300, 0.6), (600, 0.6), (610, 0.0)):
    rain_v.default_value = v; rain_v.keyframe_insert("default_value", frame=f)
tor = bpy.data.objects["FX_MouthTorrent"]
tor.hide_render = True
sun = bpy.data.objects["Key_Sun"]; wsky = sc.world.node_tree.nodes["SkyStrength"].inputs['Strength']; wt = sc.world.node_tree.nodes["SkyTint"].inputs['B']
for f, se, ss, tn, rot in ((1, 1.6, 0.8, (0.85, 0.95, 0.9), (50, 10, -30)), (280, 1.6, 0.8, (0.85, 0.95, 0.9), (50, 10, -30)),
                           (310, 0.15, 0.28, (0.55, 0.62, 0.7), (50, 10, -30)), (600, 0.15, 0.28, (0.55, 0.62, 0.7), (50, 10, -30)),
                           (2725, 4.0, 1.15, (1.0, 0.97, 0.9), (40, 0, -20)), (2929, 4.0, 1.15, (1.0, 0.97, 0.9), (40, 0, -20)),
                           (3090, 5.5, 1.3, (1.05, 0.95, 0.82), (30, 0, -35))):
    sun.data.energy = se; sun.data.keyframe_insert("energy", frame=f)
    sun.rotation_euler = tuple(R_(a) for a in rot); sun.keyframe_insert("rotation_euler", frame=f)
    wsky.default_value = ss; wsky.keyframe_insert("default_value", frame=f)
    wt.default_value = (*tn, 1); wt.keyframe_insert("default_value", frame=f)

# =============================================================== BEAT 3-4: cross-section (590-1010), BEAT 12b (2570-2725)
rl = bpy.data.objects["S3_RouteLine"]
for f, v in ((1, 0.0), (600, 0.0), (712, 1.0)):
    rl.data.bevel_factor_end = v; rl.data.keyframe_insert("bevel_factor_end", frame=f)
SUMPS = list(zip(sc["SUMP_NAMES"], sc["SUMPS"]))
for i, (nm, (zb, zf)) in enumerate(SUMPS):
    o = bpy.data.objects[nm]; f0 = 735 + i * 34; f1 = f0 + 70
    for f, h in ((1, 0.001), (f0, 0.001), (f1, zf - zb)):
        o.scale.z = h; o.keyframe_insert("scale", frame=f)
    bl = bpy.data.objects.get("S3_RouteBlue_%d" % i)
    if bl:
        mb = bl.data.materials[0].copy(); bl.data.materials[0] = mb; e_ = mb.node_tree.nodes["Emit"].inputs['Strength']
        for f, v in ((1, 0.0), (f0 + 20, 0.0), (f1, 14.0)):
            e_.default_value = v; e_.keyframe_insert("default_value", frame=f)
# 13 lights travel the route one by one (beat 12b), chamber -> entrance; reach the entrance before 2725
ROUTE = [V(p) for p in sc["ROUTE"]]
RL = [0.0]
for a, b in zip(ROUTE, ROUTE[1:]): RL.append(RL[-1] + (b - a).length)
def route_at(u):
    s = max(0.0, min(RL[-1], u * RL[-1])); i = max(j for j in range(len(RL) - 1) if RL[j] <= s)
    return ROUTE[i].lerp(ROUTE[i + 1], (s - RL[i]) / max(1e-6, RL[i + 1] - RL[i]))
for i in range(13):
    d = bpy.data.objects["S3_Dot_%02d" % i]; home = d.location.copy()
    f0 = 2575 + i * 9; f1 = f0 + 120
    for f in [1, f0] + list(range(f0 + 6, f1, 6)) + [f1, 3090]:
        if f <= f0: p = home
        else:
            u = 1.0 - min(1.0, (f - f0) / (f1 - f0)); p = route_at(u) + V((-0.06, 0, 0.0))
        d.location = p; d.keyframe_insert("location", frame=f)

# =============================================================== BEAT 5-11: chamber
HUDDLE = [("Coach", -1.0, 2.6, 15), ("Boy1", -0.3, 2.9, 0), ("Boy3", 0.4, 3.1, -10), ("Boy4", 1.6, 2.7, -25), ("Boy5", 2.3, 2.1, -40),
          ("HB1", -1.6, 1.9, 30), ("HB2", -0.9, 1.6, 20), ("HB3", -0.2, 1.4, 5), ("HB4", 2.0, 0.55, -25), ("HB5", -2.2, 2.6, 40),
          ("HB6", 0.6, 2.2, -5), ("HB7", 2.6, 3.1, -35), ("Boy2", 0.8, 1.25, -10)]
F_CH0 = 1003           # chamber first seen
F_SURF = 1085          # diver head breaks the surface
for n, x, y, yaw in HUDDLE:
    X = CX + x
    look_pool = math.degrees(math.atan2(CX + 0.2 - X, -(-1.8 - y))) - yaw   # head yaw toward the diver
    look_pool = max(-60, min(60, look_pool))
    br = random.uniform(0, 6.3)
    for f in (F_CH0 - 12, F_CH0 + 15, F_CH0 + 45, F_CH0 + 72):     # breathing, shifting, glancing around (not frozen)
        seated(n, f, X, y, yaw, lean=20 + 5 * math.sin(f * 0.05 + br), head=(12 + 9 * math.sin(f * 0.04 + br), 22 * math.sin(f * 0.031 + 2 * br)))
    shield = n in ("Boy1", "Boy4", "HB3")
    for f in (F_SURF, F_SURF + 18, F_SURF + 45, 1160, 1212):
        hov = None
        if shield and f >= F_SURF + 18:
            ev(f - 1)
            hd = RIG[n].o.matrix_world @ RIG[n].PB["head"].head
            fw = Rz(yaw + look_pool) @ V((0, -1, 0))
            hov = {"R": (hd + fw * 0.34 + V((0, 0, 0.26)) + Rz(yaw) @ V((-0.03, 0, 0)), (Rz(yaw) @ V((1, 0, 0.25))).normalized(), -fw)}
        seated(n, f, X, y, yaw, lean=10 if f > F_SURF else 22, head=(-12 if f > F_SURF else 22, look_pool if f > F_SURF else 0), hand_over=hov)
    TELE[n].add(F_CH0 - 13)
# diver A surfaces in the pool, holds the ledge edge (head torch blazing), then hauls out
DA = "DiverA"
pool = V((CX + 0.2, -1.9, 0))
for f, z, pit in ((F_CH0 - 12, -1.6, 60), (F_SURF - 20, -1.25, 40), (F_SURF, -0.95, 10), (F_SURF + 25, -0.82, 0), (1160, -0.85, 0), (1212, -0.86, 0), (1700, -0.86, 0)):
    H = HUM[DA]; P = V((pool.x, pool.y, WZ + z + 0.0)); yw = 0.0 + 180     # facing +Y (toward the boys)
    Rb = body_R(yw, pit)
    H.key_root(f, P, yaw=yw, flex=pit); H.key_spine(f, flex=-5, head=(5, 0))
    for s in "LR":
        sx = 1 if s == "L" else -1
        key_foot_free(DA, s, f, bw(DA, P, Rb, H.ankle[s] + V((0, 0.15 * math.sin(f * 0.1 + sx), 0.05))), Rb @ Rx(-50))
    hh = {}
    for s_ in "LR": key_fingers(DA, s_, f, "relaxed")
    if f >= F_SURF:
        for s in "LR":
            sx = 1 if s == "L" else -1
            ex = V((pool.x + 0.28 * sx, pool.y + 0.38, WZ - 0.06))          # treading water, hands just under the surface
            hh[s] = (ex, V((0.3 * sx, 1, -0.1)).normalized(), V((0, 0, -1)), V((ex.x + 0.5 * sx, pool.y - 0.1, WZ - 0.4)))
    key_hands(DA, f, P, Rb, hh)
TELE[DA].add(F_CH0 - 13)
# diver A then kneels by Boy2 as the medic (seen from 2017)
# divers B and C in the flooded passage (beat 6), C swims on alone into the dark (beat 7)
def pas_at(y):
    i = min(range(len(PAS)), key=lambda k: abs(PAS[k].y - y)); return PAS[i]
def pas_mid(y, up=0.75, side=0.0):
    p = pas_at(y); return V((p.x + side, y, p.z + up))
for n, y0, y1, f0, f1, up in (("DiverB", -6.0, -18.0, 1213, 1480, 0.7), ("DiverC", -7.5, -19.5, 1213, 1480, 0.75)):
    for i, f in enumerate(range(f0, f1 + 1, 10)):
        u = (f - f0) / (f1 - f0)
        y = y0 + (y1 - y0) * u; sq = math.exp(-((y + 13.0) ** 2) / 4.0)
        P = pas_mid(y, up - 0.25 * sq)
        hands = None
        if n == "DiverB" and -13.5 < y < -8.5:     # hand over hand on the guide rope
            rp = pas_mid(y - 0.35, 0.35, -0.55 * (1 - 0.6 * math.exp(-((y + 13) ** 2) / 6)))
            hands = {"R": (rp, V((0, -1, 0)), V((1, 0, 0.3)).normalized())}
            key_fingers(n, "R", f, "wrap_grip")
        elif n == "DiverB":
            key_fingers(n, "R", f, "relaxed")
        swim(n, f, P, 0.0, pitch=-6 * sq, roll=10 * sq * (1 if n == "DiverB" else -1), phase=f * 0.25, kick=1.0 - 0.6 * sq, hands=hands)
    TELE[n].add(f0 - 1)
DC = "DiverC"
for f in range(1490, 1712, 12):
    u = (f - 1490) / 220.0; y = -19.5 - 14.0 * u
    swim(DC, f, pas_mid(y, 0.7), 0.0, pitch=4, phase=f * 0.2, kick=0.9)
TELE[DC].add(1711)
tc_ = TORCH[DC]
for f, e in ((1, 70), (1500, 70), (1600, 25), (1660, 4), (1700, 0)):
    tc_.data.energy = e; tc_.data.keyframe_insert("energy", frame=f)
lensC = bpy.data.objects[DC + "_TorchLens"]
mlc = m_lens.copy(); lensC.data.materials[0] = mlc; es = mlc.node_tree.nodes["Principled BSDF"].inputs['Emission Strength']
for f, e in ((1, 25), (1500, 25), (1660, 4), (1700, 0)):
    es.default_value = e; es.keyframe_insert("default_value", frame=f)
silt_v = bpy.data.materials["M_Silt"].node_tree.nodes["SiltAmount"].outputs[0]
for f, v in ((1, 0.4), (1213, 0.5), (1300, 1.4), (1488, 1.2), (1700, 0.35), (2450, 0.4), (2520, 1.2), (2600, 0.6)):
    silt_v.default_value = v; silt_v.keyframe_insert("default_value", frame=f)

# beat 8: Boy3 kneels at the water's edge, staring at the black water (1711-2016)
B3 = "Boy3"; EDGE = V((CX + 0.3, -0.45, 0))
for f, hd in ((1705, (22, 0)), (1760, (18, 10)), (1800, (24, -8)), (1850, (16, 5)), (1900, (20, -4)), (1950, (14, 8)), (1990, (18, 0)), (2016, (20, -6))):
    g = ground_z(EDGE.x, EDGE.y)
    hh = {}
    for s in "LR":
        sx = 1 if s == "L" else -1
        hp = V((EDGE.x + 0.18 * sx, EDGE.y - 0.32, 0)); hh[s] = (V((hp.x, hp.y, ground_z(hp.x, hp.y) + 0.04)), V((0, -1, -0.3)).normalized(), V((0, 0, -1)))
    kneel(B3, f, EDGE.x, EDGE.y, 0.0, lean=30 + 4 * math.sin(f * 0.06), head=hd, hands=hh)
    for s in "LR": key_fingers(B3, s, f, "flat_palm")       # palms flat on the rock, fingers relaxed (no claw)
TELE[B3].add(1704)
# beats 9-11: team kneels around Boy2 (medic = DiverA, mask = DiverB), coach keeps a hand on the boy
P2 = V((CX + 0.8, 1.25, 0))
DIVERS_IN = 1715
# diver B swims back up the passage ahead of the rising camera (beat 8), surfaces beside the boy at the edge and waits
for f in range(1716, 1836, 10):
    u = min(1.0, (f - 1716) / 84.0); y = -9.0 + 6.4 * u
    swim("DiverB", f, pas_mid(y, 0.9 + 0.4 * u), 180.0, pitch=-12 * u, phase=f * 0.25, kick=1.0)
for f in (1850, 1900, 1950, 1995):
    H = HUM["DiverB"]; P = V((CX - 0.75, -2.35, WZ - 0.86 + 0.02 * math.sin(f * 0.1))); Rb = body_R(180 + 15, 0)
    H.key_root(f, P, yaw=195, flex=0); H.key_spine(f, flex=-4, head=(8, 25 * math.sin(f * 0.02)))
    for s in "LR":
        key_foot_free("DiverB", s, f, bw("DiverB", P, Rb, H.ankle[s] + V((0, 0.12 * math.sin(f * 0.12 + (0 if s == "L" else 3)), 0.05))), Rb @ Rx(-50))
    hh = {}
    for s in "LR":
        sx = 1 if s == "L" else -1
        ex = V((P.x + 0.28 * sx, P.y + 0.38, WZ - 0.06))
        hh[s] = (ex, V((0.3 * sx, 1, -0.1)).normalized(), V((0, 0, -1)), V((ex.x + 0.5 * sx, P.y - 0.1, WZ - 0.4)))
        key_fingers("DiverB", s, f, "relaxed")
    key_hands("DiverB", f, P, Rb, hh)
TELE["DiverB"].add(1995)
for f in (2005, 2017, 2060, 2110, 2154):
    kneel("DiverB", f, P2.x - 0.45, P2.y - 0.45, 135, lean=24 + 6 * math.sin(f * 0.045), head=(22 + 8 * math.sin(f * 0.05), 14 * math.sin(f * 0.03)))
for f in (DIVERS_IN, 1800, 1900, 1990, 2017, 2060, 2110, 2154):    # leaning in, nodding, looking at each other and the boy
    kneel(DA, f, P2.x + 0.42, P2.y + (-0.3 if f >= 2110 else 0.02), -82, lean=(52 if f >= 2110 else 40) + 3 * math.sin(f * 0.04 + 1), head=(26 + 6 * math.sin(f * 0.06), -14 * math.sin(f * 0.035 + 1)))
TELE[DA].add(DIVERS_IN - 1)
for n, x, y, yaw in HUDDLE:
    if n in ("Boy3",): continue
    X = CX + x
    ph = (hash(n) % 100) / 16.0
    for f in (1245, DIVERS_IN, 1800, 1890, 1980, 2017, 2070, 2120, 2180, 2240, 2300, 2360, 2406):
        if n == "Boy2" and f >= 2155: continue
        seated(n, f, X, y, yaw, lean=21 + 4 * math.sin(f * 0.05 + ph),
               head=(10 + 8 * math.sin(f * 0.04 + ph), 20 * math.sin(f * 0.025 + ph)) if n != "Boy2" else (5, 10))
# beat 10: sedation (2155-2328): medic's right hand with the syringe at Boy2's left upper arm, left hand steadies; boy's eyes close
ev(2155)
def bone_w(n, b, t=0.0):
    pb = RIG[n].PB[b]; return RIG[n].o.matrix_world @ (pb.head.lerp(pb.tail, t))
bpy.ops.mesh.primitive_cylinder_add(radius=0.006, depth=0.09)
syr = bpy.context.active_object; syr.name = "Prop_Syringe"
syr.data.materials.append(bpy.data.materials.get("M_Visor"))
bpy.ops.mesh.primitive_cylinder_add(radius=0.0012, depth=0.03, location=(0, 0, -0.06)); ndl = bpy.context.active_object; ndl.name = "Prop_Needle"
ndl.data.materials.append(bpy.data.materials.get("M_Tank")); ndl.parent = syr
for f in (2155, 2190, 2230, 2270, 2300, 2328):
    ev(f)
    arm = bone_w("Boy2", "upperarm02.L", 0.5)
    outw = (arm - bone_w("Boy2", "spine02")).normalized(); outw.z = 0; outw.normalize()
    inj = arm + outw * 0.05
    tip = inj + outw * (0.03 if 2190 <= f <= 2270 else 0.12)
    W = tip + outw * 0.09 + V((0, 0, 0.02))
    HUM[DA].key_hand("R", f, W, -outw, V((0, 0, 1)), W + V((0.3, 0.3, -0.4)))
    key_fingers(DA, "L", f, "relaxed")
    # medic's free (left) hand: relaxed at his side, outside the thigh (it could not reach the boy's shoulder)
    rpb = RIG[DA].PB["root"]; Pm = RIG[DA].o.matrix_world @ rpb.head
    Rm = (rpb.matrix.to_3x3() @ RIG[DA].rest("root").to_3x3().inverted()).normalized()
    Wl, dl, nl = relaxed_hand(DA, Pm, Rm, "L", out=0.16, up=0.12)
    HUM[DA].key_hand("L", f, Wl, dl, nl, elbow_pole(DA, Pm, Rm, "L", out=0.35))
    # syringe in the medic's right hand (shared grip_object: pinches the thin barrel, thumb opposing)
    syr.location = tip + outw * 0.055; syr.rotation_euler = (-outw).to_track_quat('-Z', 'Y').to_euler()
    syr.keyframe_insert("location", frame=f); syr.keyframe_insert("rotation_euler", frame=f)
    ev(f); grip_object(RIG[DA].o, "R", f, syr, syr.matrix_world.translation + outw * 0.02, -V((0, 0, 1)))
for s_ in "LR": key_fingers(DA, s_, 2340, "relaxed")       # syringe handed off: hands relax
for s_ in "LR": key_fingers("DiverB", s_, 2410, "relaxed")   # straps done: hands relax before the tow grip
for f, h in ((1, True), (2150, False), (2335, True)):
    syr.hide_render = h; syr.keyframe_insert("hide_render", frame=f); ndl.hide_render = h; ndl.keyframe_insert("hide_render", frame=f)
for f, a in ((2155, 0), (2280, 0), (2320, 1)):
    for s in "LR":
        RIG["Boy2"].key_rot("orbicularis03." + s, f, [("X", 28 * a)])
for f in (2345, 2406):
    kneel(DA, f, P2.x + 0.42, P2.y + (-0.3 if f < 2400 else 0.05), -82, lean=(48 if f < 2400 else 24), head=(20, 0))
for f, hd in ((2155, (5, 10)), (2290, (5, 10)), (2328, (25, 18)), (2406, (28, 20))):
    seated("Boy2", f, P2.x, P2.y, -10, lean=14, head=hd, hug=False)
# beat 11: full-face mask fitted (2329-2406) by DiverB, then lift (2380+)
bpy.ops.mesh.primitive_torus_add(major_radius=0.068, minor_radius=0.012, major_segments=40, minor_segments=10, rotation=(R_(90), 0, 0))
fm_ = bpy.context.active_object; fm_.name = "Prop_FullFaceMask"; fm_.data.transform(Matrix.Diagonal((1.0, 1.0, 1.32, 1))); fm_.data.materials.append(m_mask)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=32, ring_count=16)
vz = bpy.context.active_object; vz.name = "Prop_MaskVisor"; vz.data.transform(Matrix.Diagonal((0.068, 0.04, 0.09, 1)))
_bv = bmesh.new(); _bv.from_mesh(vz.data); bmesh.ops.delete(_bv, geom=[v_ for v_ in _bv.verts if v_.co.y > 0.002], context='VERTS'); _bv.to_mesh(vz.data); _bv.free()
vz.data.materials.append(m_visor); vz.parent = fm_
bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=0.05, location=(0, -0.065, -0.07), rotation=(R_(90), 0, 0))
rg = bpy.context.active_object; rg.name = "Prop_MaskRegulator"; rg.data.materials.append(m_mask); rg.parent = fm_
ev(2365)
hb2 = RIG["Boy2"].PB["head"]; HM = RIG["Boy2"].o.matrix_world @ hb2.matrix
_ri = RIG["Boy2"].BN["head"].matrix_local.inverted().to_3x3()
_fl, _ul, _sl = _ri @ V((0, -1, 0)), _ri @ V((0, 0, 1)), _ri @ V((1, 0, 0))
face_local = V((0, -0.035, 0.11))    # in head-bone space: y along the bone (up), -z/... resolved below
body2 = bpy.data.objects["Boy2.body"]
hc = HM @ V((0, 0.09, 0)); fwd2 = (HM.to_3x3() @ _fl).normalized()
hit, loc, nrm, idx = body2.evaluated_get(bpy.context.evaluated_depsgraph_get()).ray_cast(RIG["Boy2"].o.matrix_world.inverted() @ (hc + fwd2 * 0.5), -fwd2)
face_w = (RIG["Boy2"].o.matrix_world @ loc) if hit else hc + fwd2 * 0.1
upv = (HM.to_3x3() @ _ul).normalized()
_x = fwd2.cross(upv).normalized() * -1; _up = _x.cross(-fwd2) * -1
Mface = Matrix.Translation(face_w + fwd2 * 0.012 + upv * 0.01) @ Matrix((_x, -fwd2, upv)).transposed().to_4x4()
for f, u in ((1, 0.0), (2329, 0.0), (2365, 1.0)):
    start = Matrix.Translation(face_w + fwd2 * 0.32 + V((0, 0, -0.05))) @ Mface.to_3x3().to_4x4()
    M = start.lerp(Mface, u) if hasattr(start, "lerp") else (Mface if u > 0.5 else start)
    fm_.matrix_world = M
    fm_.keyframe_insert("location", frame=f); fm_.keyframe_insert("rotation_euler", frame=f)
for f, h in ((1, True), (2325, False), (2600, True)):
    for o in (fm_, vz, rg):
        o.hide_render = h; o.keyframe_insert("hide_render", frame=f)
for f in (2329, 2345, 2365, 2385, 2406):
    ev(f)
    c_ = fm_.matrix_world.translation; side = (HM.to_3x3() @ _sl).normalized()
    for s in "LR":
        sx = 1 if s == "L" else -1
        key_fingers("DiverB", s, f, "pinch")
        if f < 2380:
            W = c_ + side * (0.11 * -sx) + fwd2 * 0.02 + V((0, 0, -0.02))
            ev(f); cpt = c_ + side * (0.075 * -sx)
            grip_object(RIG["DiverB"].o, s, f, fm_, cpt, (side * sx).normalized())        # fingers close on the mask rim
        else:      # pull the straps behind the head
            W = c_ - fwd2 * 0.13 + side * (0.1 * -sx) + V((0, 0, 0.05))
            HUM["DiverB"].key_hand(s, f, W, (fwd2 * -1 + V((0, 0, 0.3))).normalized(), side * sx, W + fwd2 * 0.6 + side * 0.4 * -sx)
# =============================================================== BEAT 12: tow through the flooded passage (2407-2570)
# DiverB swims, Boy2 lies face-up in the harness beside him (head first), the mask stays on the boy's head
# hold seated / kneeling until the camera dives through the water surface (2421), then the tow is under way
kneel("DiverB", 2415, P2.x - 0.45, P2.y - 0.45, 135, lean=30, head=(25, 0))
seated("Boy2", 2415, P2.x, P2.y, -10, lean=14, head=(28, 20), hug=False)
TOW0, TOW1 = 2421, 2570
# tow harness: a webbing handle on the boy's chest (Child Of spine02), the diver grips it
bpy.ops.mesh.primitive_torus_add(major_radius=0.045, minor_radius=0.011, major_segments=24, minor_segments=8, rotation=(R_(90), 0, 0))
harness = bpy.context.active_object; harness.name = "Prop_TowHarness"; harness.data.materials.append(m_strap_h)
harness.location = rest_head("Boy2", "spine02") + V((0, -0.16, 0.0))
rest_attach(harness, "Boy2", "spine02")
for f_, h_ in ((1, True), (2415, True), (2416, False), (2575, True)):
    harness.hide_render = h_; harness.keyframe_insert("hide_render", frame=f_)
for f in range(TOW0, TOW1 + 1, 10):
    u = (f - TOW0) / (TOW1 - TOW0); y = -1.6 - 10.3 * u      # starts behind the diving camera, swims into frame
    sq = math.exp(-((y + 13.0) ** 2) / 4.0)
    P = pas_mid(y, 0.85 - 0.2 * sq, 0.3)
    swim("DiverB", f, P, 0.0, phase=f * 0.25, kick=0.9)
    Pb = pas_mid(y - 0.1, 0.4 - 0.12 * sq, 0.12)                # just below the diver, harness within reach
    H = HUM["Boy2"]; Rb = body_R(180, -88)
    H.key_root(f, Pb, yaw=180, flex=-88); H.key_spine(f, flex=0, head=(0, 0))
    for s in "LR":
        key_foot_free("Boy2", s, f, bw("Boy2", Pb, Rb, H.ankle[s]), Rb)
    key_hands("Boy2", f, Pb, Rb, {s: relaxed_hand("Boy2", Pb, Rb, s, out=0.02) for s in "LR"})
    # diver's left hand on the harness at the boy's chest
    ch_ = bw("Boy2", Pb, Rb, rest_head("Boy2", "spine02")) + V((0, 0, 0.12))
    ev(f); hpt = harness.matrix_world.translation
    grip_object(RIG["DiverB"].o, "L", f, harness, hpt, V((0, 0, -1)))                          # fingers wrap the harness handle
    key_elbow("DiverB", "L", f, hpt + V((0.5, 0.3, 0.4)))
for n in ("DiverB", "Boy2"): TELE[n].add(TOW0 - 1)
# mask: Child Of Boy2's head from the fitting onward
ev(2366)
cmask = fm_.constraints.new('CHILD_OF'); cmask.target = RIG["Boy2"].o; cmask.subtarget = "head"
cmask.inverse_matrix = (RIG["Boy2"].o.matrix_world @ RIG["Boy2"].PB["head"].matrix).inverted()
for f, v in ((1, 0.0), (2365, 0.0), (2366, 1.0)):
    cmask.influence = v; cmask.keyframe_insert("influence", frame=f)
# bubbles from the regulator (2370-2570)
m_bub = bpy.data.materials.new("M_Bubble"); m_bub.use_nodes = True
_bp = m_bub.node_tree.nodes["Principled BSDF"]; _bp.inputs['Transmission Weight'].default_value = 1.0; _bp.inputs['Roughness'].default_value = 0.0; _bp.inputs['IOR'].default_value = 1.0
for i in range(16):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.006 + 0.008 * random.random(), segments=10, ring_count=6)
    b = bpy.context.active_object; b.name = "FX_Bubble_%02d" % i; b.data.materials.append(m_bub)
    ph = random.random()
    for f in range(2370, 2580, 8):
        ev(f); base = rg.matrix_world.translation
        a = ((f - 2370) / 70.0 + ph) % 1.0
        b.location = base + V((0.03 * math.sin(i + f * 0.2), 0.03 * math.cos(i * 2 + f * 0.17), 0.05 + 0.6 * a))
        b.keyframe_insert("location", frame=f)
    for f, h in ((1, True), (2370, False), (2580, True)):
        b.hide_render = h; b.keyframe_insert("hide_render", frame=f)

# =============================================================== BEAT 13: out of the mouth into daylight (2725-2928)
m_canvas = bpy.data.materials.new("M_Stretcher"); m_canvas.use_nodes = True
m_canvas.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.75, 0.35, 0.08, 1)
bpy.ops.mesh.primitive_cube_add(size=1); stre = bpy.context.active_object; stre.name = "Prop_Stretcher"
stre.data.transform(Matrix.Diagonal((0.55, 2.0, 0.04, 1))); stre.data.materials.append(m_canvas)
stre.data.materials.append(bpy.data.materials["M_Tank"])
import bmesh as _bm_
_sb = _bm_.new(); _sb.from_mesh(stre.data)
for sx in (-1, 1):
    r_ = _bm_.ops.create_cone(_sb, cap_ends=True, segments=10, radius1=0.018, radius2=0.018, depth=2.5,
                              matrix=Matrix.Translation((0.29 * sx, 0, 0.0)) @ Matrix.Rotation(R_(90), 4, 'X'))
    for v_ in r_['verts']:
        for f_ in v_.link_faces: f_.material_index = 1
_sb.to_mesh(stre.data); _sb.free()
# carriers walk out of the mouth: DiverA front, DiverB back, stretcher between at hip height, Boy4 lying on it
OUT0, OUT1 = 2725, 2928
def carry_path(f, off):
    u = (f - OUT0) / (OUT1 - OUT0); y = 3.0 - 13.0 * u + off; x = 0.2 * math.sin(u * 3)
    return V((x, y, 0))
for n, off in (("DiverA", -1.36), ("DiverB", 1.36)):
    H = HUM[n]
    H.walk(lambda f, off=off: carry_path(f, off), lambda f: 0.0, OUT0, OUT1, stride=0.7, lift=0.07, lean=4, step=2)
    TELE[n].add(OUT0 - 1)
for f in range(OUT0, OUT1 + 1, 6):
    a = carry_path(f, -1.36); b = carry_path(f, 1.36)
    ga, gb = ground_z(a.x, a.y), ground_z(b.x, b.y)
    pa = V((a.x, a.y, ga + 1.0)); pb_ = V((b.x, b.y, gb + 1.0)); mid = (pa + pb_) / 2
    d_ = (pa - pb_).normalized()
    stre.location = mid; stre.rotation_euler = V((0, -1, 0)).rotation_difference(d_).to_euler()
    stre.keyframe_insert("location", frame=f); stre.keyframe_insert("rotation_euler", frame=f)
    sdv = d_.cross(V((0, 0, 1))).normalized()
    for n, end, inward in (("DiverA", mid + d_ * 1.22, -d_), ("DiverB", mid - d_ * 1.22, d_)):
        for s in "LR":
            sx = 1 if s == "L" else -1
            pole_pt = end + sdv * (0.29 * (1 if (s == "L") == (n == "DiverB") else -1))       # centre of the pole
            ev(f); grip_object(RIG[n].o, s, f, stre, pole_pt, V((0, 0, -1)))                     # fingers wrap the pole from above
            key_elbow(n, s, f, pole_pt + V((0.4 * (1 if pole_pt.x > mid.x else -1), 0, -0.2)) - inward * 0.25)
    # Boy4 lies on the stretcher (face up, head toward the front carrier)
    H = HUM["Boy4"]; Rb = body_R(0, -88) ; Pboy = mid + V((0, 0.15, 0.0))
    H.key_root(f, Pboy, yaw=0, flex=-88); H.key_spine(f, head=(-5, 0))
    for s in "LR": key_foot_free("Boy4", s, f, bw("Boy4", Pboy, Rb, H.ankle[s]), Rb)
    hb4 = {}
    for s in "LR":
        sx = 1 if s == "L" else -1
        W = bw("Boy4", Pboy, Rb, rest_head("Boy4", "spine04") + V((0.1 * sx, -0.22, 0.02)))
        hb4[s] = (W, Rb @ V((-sx, 0, 0.2)).normalized(), Rb @ V((0, 1, 0)), W + Rb @ V((0.4 * sx, 0.2, 0)))
    key_hands("Boy4", f, Pboy, Rb, hb4)
TELE["Boy4"].add(OUT0 - 1)
for o in [stre]:
    for f, h in ((1, True), (OUT0 - 1, True), (OUT0, False)):
        o.hide_render = h; o.keyframe_insert("hide_render", frame=f)
# cheering crowd at the clearing edge, boys already out wrapped and waving
CR = [("Crowd1", -3.2, -11.0, 30), ("Crowd2", -4.4, -12.2, 50), ("Crowd3", 3.6, -11.5, -40), ("Crowd4", 4.8, -13.0, -55),
      ("Boy1", -2.4, -14.5, 15), ("Boy5", 2.2, -15.0, -20), ("Coach", 1.0, -16.0, 0)]
for n, x, y, yaw in CR:
    H = HUM[n]
    for k, f in enumerate(range(OUT0, OUT1 + 165, 15)):
        g = ground_z(x, y); P = V((x, y + 0.0, g + H.root_head.z - 0.02 - 0.03 * (k % 2))); Rb = body_R(yaw, -4)
        H.key_root(f, P, yaw=yaw, flex=-4); H.key_spine(f, flex=-6, head=(-10, 0))
        for s in "LR":
            sx = 1 if s == "L" else -1
            H.key_foot(s, f, H.foot_xy(s, P, yaw), yaw)
        cheer = (k + hash(n) % 3) % 2
        hh = {}
        for s in "LR":
            sx = 1 if s == "L" else -1
            sh = bw(n, P, Rb, rest_head(n, "upperarm01." + s))
            if n.startswith("Crowd"):          # clapping in front of the chest
                gap = 0.05 if cheer else 0.2
                W = bw(n, P, Rb, rest_head(n, "spine02")) + Rb @ V((gap / 2 * sx, -0.32, 0.12))
                hh[s] = (W, Rb @ V((-0.2 * sx, -0.3, 1)).normalized(), Rb @ V((-sx, 0, 0)), sh + Rb @ V((0.45 * sx, 0.2, -0.35)))
                key_fingers(n, s, f, "flat_palm")
            elif s == "R":                         # rescued boys / coach: an open-palm wave at head height
                W = sh + Rb @ V((0.34 * sx + 0.06 * (cheer - 0.5), -0.22, 0.22)); hh[s] = (W, Rb @ V((0.15 * sx, 0, 1)).normalized(), Rb @ V((0, -1, 0)), sh + Rb @ V((0.55 * sx, 0.3, -0.25)))   # wave out to the side, well clear of the face
                key_fingers(n, s, f, "relaxed")
        key_hands(n, f, P, Rb, hh)
    TELE[n].add(OUT0 - 1)
heli = bpy.data.objects["S1_Heli"]; rotor = bpy.data.objects["S1_Heli_Rotor"]
for f, loc in ((1, (2, -44, 30)), (2725, (6, -40, 14)), (2860, (3, -30, 4.5)), (2928, (3, -29, 0.6 + ground_z(3, -29))), (3090, (3, -29, 0.6 + ground_z(3, -29)))):
    heli.location = loc; heli.keyframe_insert("location", frame=f)
rotor.rotation_euler.z = 0; rotor.keyframe_insert("rotation_euler", frame=1)
rotor.rotation_euler.z = R_(360 * 0.6 * 3090 / 60 * 6); rotor.keyframe_insert("rotation_euler", frame=3090)
for fc in rotor.animation_data.action.layers[0].strips[0].channelbags[0].fcurves:
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
for nm in ("M_BeaconRed", "M_BeaconBlue"):
    e_ = bpy.data.materials[nm].node_tree.nodes["Emit"].inputs['Strength']
    for f in range(2700, 3091, 10):
        e_.default_value = 30.0 if ((f // 10) % 2) == (nm == "M_BeaconRed") else 0.5; e_.keyframe_insert("default_value", frame=f)

# =============================================================== parking (everyone not on set is far away), stepped jumps
USED = {}
def on_set(n, f0, f1): USED.setdefault(n, []).append((f0, f1))
SPANS = {"Coach": [(1, 590), (990, 2406), (2725, 3090)], "Boy1": [(1, 590), (990, 2406), (2725, 3090)], "Boy2": [(1, 590), (990, 2570)],
         "Boy3": [(1, 590), (990, 2406)], "Boy4": [(1, 590), (990, 2406), (2725, 3090)], "Boy5": [(1, 590), (990, 2406), (2725, 3090)],
         "DiverA": [(990, 2406), (2725, 3090)], "DiverB": [(1212, 1488), (1714, 2570), (2725, 3090)], "DiverC": [(1212, 1711)]}
for n in HB: SPANS[n] = [(990, 2406)]
for n in CROWD: SPANS[n] = [(2725, 3090)]
for n, spans in SPANS.items():
    edges = []
    prev_end = 0
    for (a, b) in spans:
        if a - 1 > prev_end + 1:
            park(n, max(1, prev_end + 1)); park(n, a - 1); TELE[n].add(a - 1)
            if prev_end > 0: TELE[n].add(prev_end)
        prev_end = b
    if prev_end < 3090:
        park(n, prev_end + 1); park(n, 3090); TELE[n].add(prev_end)
# Boy3 is kneeling 1705-2016, so its huddle keys after 1704 must not fight: keys exist only up to 1212 + kneel keys; fine.
def stepped(obj, frames):
    ad = obj.animation_data
    if not ad or not ad.action: return
    for layer in ad.action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    for kp in fc.keyframe_points:
                        if int(round(kp.co.x)) in frames: kp.interpolation = 'CONSTANT'
                    # also the last key at or before each jump frame
                    xs = [kp.co.x for kp in fc.keyframe_points]
                    for j in frames:
                        prev = [kp for kp in fc.keyframe_points if kp.co.x <= j + 0.01]
                        if prev: prev[-1].interpolation = 'CONSTANT'
for n in ALL:
    stepped(RIG[n].o, TELE[n])
sc["TELE"] = {n: sorted(v) for n, v in TELE.items()}
# water surface seen from below: no bright total-internal-reflection sheet, just a dim green transmissive skin
_mw = bpy.data.materials["M_WaterSurface"]; _n, _l = _mw.node_tree.nodes, _mw.node_tree.links
_o = next(x for x in _n if x.type == 'OUTPUT_MATERIAL'); _src = _o.inputs['Surface'].links[0].from_socket
_g = _n.new('ShaderNodeNewGeometry'); _t = _n.new('ShaderNodeBsdfTransparent'); _t.inputs['Color'].default_value = (0.3, 0.36, 0.3, 1)
_mx = _n.new('ShaderNodeMixShader'); _l.new(_g.outputs['Backfacing'], _mx.inputs['Fac']); _l.new(_src, _mx.inputs[1]); _l.new(_t.outputs[0], _mx.inputs[2])
_l.new(_mx.outputs[0], _o.inputs['Surface'])
# dim ambient glow along the flooded passage (murk scatters it: silhouettes without a white-out)
for i, y in enumerate((-4.0, -11.0, -18.0, -26.0)):
    p_ = pas_mid(y, 1.4); L_ = bpy.data.objects.new("S5_Ambient_%d" % i, bpy.data.lights.new("S5_Ambient_%d" % i, 'POINT'))
    L_.data.energy = 12; L_.data.color = (0.55, 0.7, 0.75); L_.data.shadow_soft_size = 1.0; L_.location = p_; sc.collection.objects.link(L_)
# chamber fill
f4 = bpy.data.objects["S4_Fill"]; f4.data.energy = 90; f4.visible_volume_scatter = False; f4.data.color = (0.85, 0.9, 1.0)
EXPO = [(1, 0.0), (290, 0.0), (330, 0.8), (580, 0.8), (583, 0.0), (1008, 0.0), (1009, 1.0), (1212, 1.0), (1240, 1.0), (1700, 1.0), (1840, 1.0),
        (2430, 1.0), (2470, 1.0), (2565, 1.0), (2566, 0.0), (2726, 0.0), (2727, 0.6), (2800, 0.0), (3090, 0.0)]
for f, e in ((1, 150), (1212, 150), (1218, 0), (1878, 0), (1886, 150), (2430, 150), (2438, 0), (2565, 0)):
    f4.data.energy = e; f4.data.keyframe_insert("energy", frame=f)
for f, v in EXPO:
    sc.view_settings.exposure = v; sc.view_settings.keyframe_insert("exposure", frame=f)

exec(open(os.path.join(HERE, "03b_camera.py")).read())
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ANIM_OK")
