"""B23 animation, props, cameras and look. Every action is keyed at an offset from its shot's start (timing.py), 1x speed.
blender -b sets.blend --python 03_anim.py -- <out.blend>"""
import sys, os, math, random, json
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion, noise
HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.join(HERE, "..", "..", "pipeline")
exec(open(os.path.join(HERE, "00_lib.py")).read())
exec(open(os.path.join(PIPE, "anim_lib.py")).read())
exec(open(os.path.join(PIPE, "hand_poses.py")).read())
exec(open(os.path.join(HERE, "timing.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
sc.frame_start = 1; sc.frame_end = END_FRAME
ST = START; SE = shot_end
V = lambda *a: Vector(a)
CUR_S = [1.0]
random.seed(23)

def ground_z(x, y): return 0.0
_kf0 = Human.key_foot
def _kf(self, s, f, xy, yaw, lift=0.0, pitch=0.0):     # MPFB shoe soles dip ~2 cm below the ankle-derived floor line
    _kf0(self, s, f, xy, yaw, lift + 0.03 / CUR_S[0], pitch)
Human.key_foot = _kf
_kr0 = Human.key_root
def _kr(self, f, pos, yaw=0.0, flex=0.0, side=0.0):
    _kr0(self, f, Vector((pos.x, pos.y, pos.z + 0.03 / CUR_S[0])), yaw=yaw, flex=flex, side=side)
Human.key_root = _kr

def yaw_to(d): return math.degrees(math.atan2(d.x, -d.y))
def Rz(yaw): return Matrix.Rotation(R_(yaw), 3, 'Z')

def fcurves_of(act):
    try: return list(act.fcurves)
    except Exception:
        out = []
        for L_ in act.layers:
            for st in L_.strips:
                for cb in st.channelbags: out += list(cb.fcurves)
        return out
def const_interp(idb):
    ad = idb.animation_data
    if ad and ad.action:
        for fc in fcurves_of(ad.action):
            for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
def lin_interp(idb):
    ad = idb.animation_data
    if ad and ad.action:
        for fc in fcurves_of(ad.action):
            for k in fc.keyframe_points: k.interpolation = 'LINEAR'

def body_height(rig):
    body = next(c for c in rig.children if c.type == 'MESH' and c.name.endswith("body"))
    dg = bpy.context.evaluated_depsgraph_get(); e = body.evaluated_get(dg)
    zs = [(body.matrix_world @ v.co).z for v in e.data.vertices]
    return max(zs) - min(zs)

class Char:
    def __init__(self, name, height):
        self.o = bpy.data.objects[name]
        self.o.location = (0, 0, 0); self.o.rotation_euler = (0, 0, 0); self.o.scale = (1, 1, 1)
        bpy.context.view_layer.update()
        self.s = height / body_height(self.o)
        self.o.scale = (self.s,) * 3
        self.R = Rig(self.o); self.H = Human(self.R)
        for pb in self.o.pose.bones: pb.rotation_mode = 'QUATERNION'
        self.used = set()
    def use(self): CUR_S[0] = self.s; return self
    def a(self, v): return Vector(v) / self.s
    def stand(self, f, pos_w, yaw, crouch=0.02, flex=3.0, head=(0.0, 0.0), twist=0.0, stance=1.0, side=0.0):
        self.use(); P = self.a((pos_w[0], pos_w[1], 0))
        self.H.key_root(f, Vector((P.x, P.y, self.H.root_head.z - crouch / self.s)), yaw=yaw, flex=flex * 0.5, side=side)
        self.H.key_spine(f, flex=flex, twist=twist, head=head)
        for sd in "LR":
            xy = self.H.foot_xy(sd, Vector((P.x, P.y, 0)), yaw)
            if stance != 1.0:
                c = Vector((P.x, P.y)); xy = c + (xy - c) * stance
            self.H.key_foot(sd, f, xy, yaw)
    def kneel(self, f, pos_w, yaw, lean=0.0, head=(0.0, 0.0), twist=0.0, hip=0.50):
        """upright kneel: knees on the ground under the hips, shins back, toes tucked"""
        self.use(); R3 = Rz(yaw)
        P = self.a((pos_w[0], pos_w[1], 0))
        self.H.key_root(f, Vector((P.x, P.y, hip / self.s)), yaw=yaw, flex=lean * 0.4)
        self.H.key_spine(f, flex=lean, twist=twist, head=head)
        for sd, sx in (("L", 1), ("R", -1)):
            ank = Vector(pos_w[:2]).to_3d() + R3 @ V(sx * 0.11, 0.40, 0)
            self.H.key_foot(sd, f, self.a(ank).to_2d(), yaw, lift=0.07 / self.s, pitch=62)
            # knee pole straight ahead
            pole = Vector(pos_w[:2]).to_3d() + R3 @ V(sx * 0.12, -0.8, 0.1)
            pb = self.R.PB["Pole_knee." + sd]; n = "Pole_knee." + sd
            pb.location = self.R.rest(n).to_3x3().inverted() @ (self.a(pole) - self.R.BN[n].head_local)
            pb.keyframe_insert("location", frame=f, group=n)
    def world_bone(self, n, f=None):
        if f is not None: sc.frame_set(int(f))
        return self.o.matrix_world @ self.o.pose.bones[n].matrix
    def hand_w(self, s, f, W, d, n, pole_w=None):
        self.use(); R3 = self.o.matrix_world.to_3x3().normalized().inverted()
        self.H.key_hand(s, f, self.a(W), R3 @ Vector(d), R3 @ Vector(n), None if pole_w is None else self.a(pole_w))
    def hang(self, f, pos_w, yaw, swing=(0.0, 0.0), out=0.11, which="LR", fwd=0.0):
        R3 = Rz(yaw)
        for i, sd in enumerate("LR"):
            if sd not in which: continue
            sx = 1 if sd == "L" else -1
            sh = self.o.data.bones["upperarm01." + sd].head_local * self.s
            W = V(pos_w[0], pos_w[1], 0) + R3 @ V(sx * (abs(sh.x) + out * self.s / 1.2), -0.11 - swing[i] - fwd, sh.z - 0.50 * self.s + 0.5 * abs(swing[i]) ** 2 + fwd * 0.4)
            d = R3 @ V(0, -0.15 - swing[i] * 0.6 - fwd, -1).normalized(); n = R3 @ V(-sx, 0, 0)
            pole = V(pos_w[0], pos_w[1], 0) + R3 @ V(sx * 0.45 * self.s, 0.5, sh.z - 0.3 * self.s)
            self.hand_w(sd, f, W, d, n, pole)
    def shoulder_w(self, sd, pos_w, yaw, f=None):
        """approximate world shoulder for a standing pose at pos_w/yaw"""
        sh = self.o.data.bones["upperarm01." + sd].head_local * self.s
        return V(pos_w[0], pos_w[1], 0) + Rz(yaw) @ V(sh.x, sh.y, sh.z)
    def jaw(self, f, open_=0.0):
        if "jaw" in self.o.pose.bones:
            self.R.key_rot("jaw", f, [("X", 9 * open_)])

def walk(c, f0, f1, p0, p1, yaw=None, stride=0.72, swing=0.17, arms="LR", out=0.11, lift=0.08, lean=5.0):
    """1x walk from p0 to p1 (world xy) with bent-arm swing"""
    p0 = Vector(p0).to_3d(); p1 = Vector(p1).to_3d()
    yw = yaw if yaw is not None else yaw_to(p1 - p0)
    path = lambda f: p0.lerp(p1, min(1.0, max(0.0, (f - f0) / max(1, f1 - f0))))
    c.use(); c.H.walk(lambda f: c.a(path(f)), lambda f: yw, f0, f1, stride=stride / c.s, lift=lift / c.s, bob=0.018 / c.s, crouch=0.004 / c.s, lean=lean)
    dist = (p1 - p0).to_2d().length
    for f in sorted(set(list(range(f0, f1 + 1, 3)) + [f1])):
        u = (f - f0) / max(1, f1 - f0); ph = 2 * math.pi * (u * dist / stride)
        sw = swing * math.sin(ph)
        c.hang(f, path(f), yw, swing=(sw, -sw), out=out, which=arms, fwd=0.06)
    return path

def child_of_now(obj, rig, bone, f):
    sc.frame_set(int(f))
    mw = obj.matrix_world.copy()
    c = obj.constraints.new('CHILD_OF'); c.target = rig; c.subtarget = bone
    bpy.context.view_layer.update()
    PBm = rig.matrix_world @ rig.pose.bones[bone].matrix
    c.inverse_matrix = PBm.inverted()
    obj.matrix_world = mw
    bpy.context.view_layer.update()
    return c

def vis_only(objs, ranges):
    """visible only inside the given (f0, f1) ranges"""
    for o in objs:
        key_vis(o, 1, False)
        for a, b in ranges:
            key_vis(o, a, True); key_vis(o, b + 1, False)
        const_interp(o)

# =========================================================================== characters
W = Char("Warrior", 1.78)
EL = Char("Elder", 1.68); VW = Char("VillagerW", 1.62); M1 = Char("VillagerM1", 1.74); M2 = Char("VillagerM2", 1.76)
SA = Char("SoldierA", 1.82); SB = Char("SoldierB", 1.78); SC2 = Char("Second", 1.84); SC = Char("SoldierC", 1.76)
CAST = [W, EL, VW, M1, M2, SA, SB, SC2, SC]
for c in CAST:
    for s in "LR": apply_pose(c.o, s, "relaxed", 1)
PARK = {c.o.name: V(300 + 4 * i, 300, 0) for i, c in enumerate(CAST)}
def park(c, f):
    p = PARK[c.o.name]; c.stand(f, p, 0); c.hang(f, p, 0)

# warrior: hands present in S01 only; bandages from S02
body = next(ch for ch in W.o.children if ch.name.endswith("body"))
mk = body.modifiers["HandsOff"]
for f, on in ((1, False), (ST["S02"], True)):
    mk.show_render = on; mk.show_viewport = on
    mk.keyframe_insert("show_render", frame=f); mk.keyframe_insert("show_viewport", frame=f)
const_interp(body)
BAND = [bpy.data.objects["Warrior_Bandage.L"], bpy.data.objects["Warrior_Bandage.R"]]
vis_only(BAND, [(ST["S02"], END_FRAME)])
CUT = {s: (Vector(W.o["cut_" + s]), Vector(W.o["cut_ax_" + s]), W.o["cut_rad_" + s]) for s in "LR"}

# =========================================================================== props
CP = coll("Props")
def long_prop(name, length, tip_is_wide=True, grip_from_butt=None):
    """normalise a long prop: long axis -> +Z, tip up; origin at the grip. Returns (obj, grip->tip length)"""
    o = glb_asset(name, CP)
    vs = [v.co.copy() for v in o.data.vertices]
    ext = [max(v[i] for v in vs) - min(v[i] for v in vs) for i in range(3)]; ax = max(range(3), key=lambda i: ext[i])
    lo = min(v[ax] for v in vs); hi = max(v[ax] for v in vs)
    def width(a, b):
        sl = [v for v in vs if a <= v[ax] <= b]
        if not sl: return 0
        return max(max(v[i] for v in sl) - min(v[i] for v in sl) for i in range(3) if i != ax)
    K = 12; ws = [width(lo + (hi - lo) * k / K, lo + (hi - lo) * (k + 1) / K) for k in range(K)]
    kw = max(range(K), key=lambda k: ws[k])
    wide_hi = kw >= K / 2
    # rotate so the long axis is +Z with the chosen end up
    up_hi = wide_hi if tip_is_wide else not wide_hi
    M = Matrix.Identity(4)
    if ax == 0: M = Matrix.Rotation(-math.pi / 2, 4, 'Y')
    elif ax == 1: M = Matrix.Rotation(math.pi / 2, 4, 'X')
    o.data.transform(M)
    vs = [v.co for v in o.data.vertices]; zl = min(v.z for v in vs); zh = max(v.z for v in vs)
    if not up_hi:
        # the wanted tip is at the low end: flip
        o.data.transform(Matrix.Rotation(math.pi, 4, 'X'))
    vs = [v.co for v in o.data.vertices]; zl = min(v.z for v in vs); zh = max(v.z for v in vs)
    s_ = length / (zh - zl); o.data.transform(Matrix.Scale(s_, 4))
    vs = [v.co for v in o.data.vertices]; zl = min(v.z for v in vs); zh = max(v.z for v in vs)
    cx = sum(v.x for v in vs) / len(vs); cy = sum(v.y for v in vs) / len(vs)
    if grip_from_butt is None:   # sword: grip = middle of the hilt (between butt and the widest slice = guard)
        kw2 = max(range(K), key=lambda k: width(zl + (zh - zl) * k / K, zl + (zh - zl) * (k + 1) / K) if k < K / 2 else -1)
        gz = zl + (zh - zl) * (kw2 / K) * 0.5
    else:
        gz = zl + grip_from_butt
    o.data.transform(Matrix.Translation(V(-cx, -cy, -gz)))
    o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0)
    return o, zh - gz, gz - zl

def frame_from(z_dir, y_hint):
    z = Vector(z_dir).normalized(); y = (Vector(y_hint) - z * Vector(y_hint).dot(z)).normalized(); x = y.cross(z)
    return Matrix((x, y, z)).transposed()

# sword (soldier A in S01/S03, the second-in-command in S14)
swordA, SW_TIP, SW_BUTT = long_prop("sword", 0.92, tip_is_wide=False)
swordA.name = "SwordA"
swordB = swordA.copy(); swordB.data = swordA.data; CP.objects.link(swordB); swordB.name = "SwordB"
print("SWORD tip", round(SW_TIP, 3), "butt", round(SW_BUTT, 3))

# spears (marchers + ring guards)
spear, SP_TIP, SP_BUTT = long_prop("spear", 2.3, tip_is_wide=True, grip_from_butt=1.0)
spear.name = "SpearC"
spearB = spear.copy(); spearB.data = spear.data; CP.objects.link(spearB); spearB.name = "SpearB"

# knife strapped along each forearm (blade past the bandaged stump), leather straps around forearm + handle
knife_src, KN_TIP, KN_BUTT = long_prop("knife", 0.30, tip_is_wide=False, grip_from_butt=0.0)
knife_src.name = "KnifeSrc"; knife_src.hide_render = True; knife_src.hide_viewport = True
LEATHER = flat("Leather", (0.28, 0.14, 0.06), rough=0.65)
def strap_ring(name, centre, ax, pts, width=0.022):
    u = (V(0, 0, 1) - ax * ax.z).normalized(); w_ = ax.cross(u)
    p2 = [((p - centre).dot(u), (p - centre).dot(w_)) for p in pts]
    # convex hull (monotone chain)
    p2 = sorted(set((round(a, 4), round(b, 4)) for a, b in p2))
    def cross(o_, a, b): return (a[0] - o_[0]) * (b[1] - o_[1]) - (a[1] - o_[1]) * (b[0] - o_[0])
    lo, hi = [], []
    for p in p2:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(p2):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0: hi.pop()
        hi.append(p)
    hull = lo[:-1] + hi[:-1]
    cx = sum(a for a, b in hull) / len(hull); cy = sum(b for a, b in hull) / len(hull)
    bm = bmesh.new(); r0, r1 = [], []
    for a, b in hull:
        d = Vector((a - cx, b - cy)); d = d.normalized() * (d.length + 0.004) + Vector((cx, cy))
        q = centre + u * d.x + w_ * d.y
        r0.append(bm.verts.new(q - ax * width / 2)); r1.append(bm.verts.new(q + ax * width / 2))
    n_ = len(hull)
    for i in range(n_):
        bm.faces.new([r0[i], r0[(i + 1) % n_], r1[(i + 1) % n_], r1[i]])
    o = mesh_obj(name, bm, [LEATHER], CP)
    so = o.modifiers.new("Thick", 'SOLIDIFY'); so.thickness = 0.004; so.offset = 1.0
    return o
KNIVES = []
W.o.scale = (1, 1, 1)
_muted = [cn for pb_ in W.o.pose.bones for cn in pb_.constraints if not cn.mute]   # true rest pose while parenting the knives
for cn in _muted: cn.mute = True
bpy.context.view_layer.update()
_bd = next(ch for ch in W.o.children if ch.name.endswith("body"))
_gi = {g.index: g.name for g in _bd.vertex_groups}
_skin = [_bd.matrix_world @ v.co for v in _bd.data.vertices
         if not any(_gi.get(g.group, "") in ("HelperGeometry", "JointCubes", "HANDS_OFF") for g in v.groups if g.weight > 0.1)]
for s, sx in (("L", 1), ("R", -1)):
    c, ax, rad = CUT[s]
    # real forearm skin near the strap/knife zone (rest pose): the knife and straps are sized from it, not from the cut ring
    arm = [p for p in _skin if -0.17 < (p - c).dot(ax) < 0.03 and ((p - c) - ax * (p - c).dot(ax)).length < 0.075]
    # forearm surface direction for the knife: the outside of the forearm (away from the body), level
    out = V(sx, 0, 0); out = (out - ax * out.dot(ax)).normalized()
    rb = (rad + 0.004) * 1.16
    _bobj = bpy.data.objects["Warrior_Bandage." + s]
    proj = max(((v.co - c) - ax * (v.co - c).dot(ax)).dot(out) for v in _bobj.data.vertices if -0.065 < (v.co - c).dot(ax) < 0.0)   # bandage local coords == rest positions
    base = c + out * (proj + 0.008)   # the handle lies on the rigid bandage, not on the twisting forearm skin
    print("KNIFE", s, "arm pts", len(arm), "proj", round(proj, 3), "rb", round(rb, 3))
    k = knife_src.copy(); k.data = knife_src.data; CP.objects.link(k); k.name = "Knife." + s
    k.hide_render = False; k.hide_viewport = False
    # butt 11 cm up the forearm, blade pointing past the stump along the forearm axis, flat of the blade on the arm
    Mk = Matrix.Translation(base - ax * 0.06) @ frame_from(ax, out).to_4x4()
    k.matrix_world = Mk
    # ensure the blade's flat faces the arm: the knife's thinnest local axis should be along `out`
    vs = [v.co for v in k.data.vertices]
    ex = [max(v[i] for v in vs) - min(v[i] for v in vs) for i in (0, 1)]
    if ex[0] < ex[1]:   # thin along local x -> rotate 90 deg about z so thin axis = local y (= out)
        k.matrix_world = Mk @ Matrix.Rotation(math.pi / 2, 4, 'Z')
    bpy.context.view_layer.update()
    kv = [k.matrix_world @ v.co for v in k.data.vertices]
    straps = []
    for t in (-0.048, -0.004):
        cen = c + ax * t
        kc = base + ax * (cen - base).dot(ax)            # knife's centre line at this section
        pts = [p for p in kv if abs((p - cen).dot(ax)) < 0.012 and ((p - kc) - ax * (p - kc).dot(ax)).length < 0.016]
        u = (V(0, 0, 1) - ax * ax.z).normalized(); w_ = ax.cross(u)
        band_ = bpy.data.objects["Warrior_Bandage." + s]
        pts += [v.co.copy() for v in band_.data.vertices if abs((v.co - cen).dot(ax)) < 0.013]
        straps.append(strap_ring("Strap.%s%d" % (s, len(straps)), cen, ax, pts))
    for o in [k] + straps:
        bpy.context.view_layer.update(); mw = o.matrix_world.copy()
        o.parent = W.o; o.parent_type = 'BONE'; o.parent_bone = "lowerarm02." + s
        bpy.context.view_layer.update(); o.matrix_world = mw
    KNIVES += [k] + straps
for cn in _muted: cn.mute = False
W.o.scale = (W.s,) * 3; bpy.context.view_layer.update()

# glowing iron plate (forge S08, anvil S09)
GLOW = flat("HotIron", (0.6, 0.15, 0.03), rough=0.5, emit=(1.0, 0.45, 0.08), emit_str=14.0)
def plate(name, loc):
    bm = bmesh.new(); add_box(bm, V(-0.09, -0.06, 0), V(0.09, 0.06, 0.012)); o = mesh_obj(name, bm, [GLOW], CP)
    b = o.modifiers.new("Bevel", 'BEVEL'); b.width = 0.003; b.segments = 2
    o.location = loc; return o
FORGE = Vector(sc["FORGE"]); ANV = Vector(sc["ANVIL"]); ANVT = sc["ANVIL_TOP"]
plate8 = plate("HotPlate_Forge", V(FORGE.x, FORGE.y, sc["FORGE_TOP"] + 0.03))
plate9 = plate("HotPlate_Anvil", V(ANV.x + 0.02, ANV.y - 0.04, ANVT + 0.001))
vis_only([plate8], [(1, SE("S08"))]); vis_only([plate9], [(ST("S09") if False else ST["S09"], END_FRAME)])
pl = bpy.data.lights.new("PlateGlow", 'POINT'); pl.energy = 14; pl.color = (1.0, 0.5, 0.15); pl.shadow_soft_size = 0.1
plo = bpy.data.objects.new("PlateGlow", pl); CP.objects.link(plo); plo.location = plate9.location + V(0, -0.1, 0.12)
fgl = bpy.data.lights.new("ForgeGlow", 'POINT'); fgl.energy = 35; fgl.color = (1.0, 0.45, 0.12); fgl.shadow_soft_size = 0.3
fgo = bpy.data.objects.new("ForgeGlow", fgl); CP.objects.link(fgo); fgo.location = FORGE + V(0, 0, sc["FORGE_TOP"] + 0.3)

# ---------------------------------------------------------------- emissive flames (Geometry Nodes, keyed clock T, no Scene Time)
def fire_material():
    m = bpy.data.materials.get("FireBlob")
    if m: return m
    m = bpy.data.materials.new("FireBlob"); n, l = nodes_of(m); n.clear()
    out = n.new('ShaderNodeOutputMaterial'); at = n.new('ShaderNodeAttribute'); at.attribute_type = 'INSTANCER'; at.attribute_name = "heat"
    ramp = n.new('ShaderNodeValToRGB'); el = ramp.color_ramp.elements
    el[0].position = 0.0; el[0].color = (1.0, 0.8, 0.25, 1); el[1].position = 1.0; el[1].color = (0.75, 0.08, 0.01, 1)
    mid = el.new(0.3); mid.color = (1.0, 0.45, 0.05, 1)
    em = n.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 3.0
    tr = n.new('ShaderNodeBsdfTransparent'); mx = n.new('ShaderNodeMixShader')
    pw = n.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 2.0
    l.new(at.outputs['Fac'], ramp.inputs[0]); l.new(ramp.outputs[0], em.inputs['Color'])
    l.new(at.outputs['Fac'], pw.inputs[0]); l.new(pw.outputs[0], mx.inputs[0])
    l.new(em.outputs[0], mx.inputs[1]); l.new(tr.outputs[0], mx.inputs[2]); l.new(mx.outputs[0], out.inputs[0])
    return m
FIRE_T = []
def fire_tree(name, Wd, Dp, H, N_, rad, speed):
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nd = ng.nodes; lk = ng.links
    gout = nd.new('NodeGroupOutput'); nd.new('NodeGroupInput')
    T = nd.new('ShaderNodeValue'); T.name = "T"; FIRE_T.append(ng)
    pts = nd.new('GeometryNodePoints'); pts.inputs['Count'].default_value = N_
    def rnd(lo, hi, seed):
        r = nd.new('FunctionNodeRandomValue'); r.data_type = 'FLOAT'
        mn = [s for s in r.inputs if s.name == 'Min' and s.type == 'VALUE'][0]; mx_ = [s for s in r.inputs if s.name == 'Max' and s.type == 'VALUE'][0]
        mn.default_value = lo; mx_.default_value = hi; r.inputs['Seed'].default_value = seed
        return [s for s in r.outputs if s.type == 'VALUE'][0]
    def M(op, a, b=None, c=None):
        m = nd.new('ShaderNodeMath'); m.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None: continue
            if isinstance(v, (int, float)): m.inputs[i].default_value = v
            else: lk.new(v, m.inputs[i])
        return m.outputs[0]
    x = rnd(-Wd / 2, Wd / 2, 1); y = rnd(-Dp / 2, Dp / 2, 2); ph = rnd(0, 1, 3); sp = rnd(0.7, 1.3, 4); sz = rnd(0.6, 1.3, 5)
    u = M('FRACT', M('ADD', ph, M('MULTIPLY', M('MULTIPLY', T.outputs[0], speed / H), sp)))
    shrink = M('SUBTRACT', 1.0, M('MULTIPLY', u, 0.6))
    xs = M('ADD', M('MULTIPLY', x, shrink), M('MULTIPLY', M('SINE', M('ADD', M('MULTIPLY', u, 7.0), M('MULTIPLY', ph, 40.0))), 0.05 * max(Wd, 0.3)))
    ys = M('MULTIPLY', y, shrink); z = M('MULTIPLY', u, H)
    cb = nd.new('ShaderNodeCombineXYZ'); lk.new(xs, cb.inputs[0]); lk.new(ys, cb.inputs[1]); lk.new(z, cb.inputs[2])
    lk.new(cb.outputs[0], pts.inputs['Position'])
    st = nd.new('GeometryNodeStoreNamedAttribute'); st.data_type = 'FLOAT'; st.domain = 'POINT'; st.inputs['Name'].default_value = "heat"
    lk.new(pts.outputs[0], st.inputs['Geometry']); lk.new(u, [s for s in st.inputs if s.name == 'Value'][0])
    ico = nd.new('GeometryNodeMeshIcoSphere'); ico.inputs['Radius'].default_value = 1.0; ico.inputs['Subdivisions'].default_value = 1
    sm = nd.new('GeometryNodeSetMaterial'); sm.inputs['Material'].default_value = fire_material(); lk.new(ico.outputs[0], sm.inputs['Geometry'])
    iop = nd.new('GeometryNodeInstanceOnPoints'); lk.new(st.outputs[0], iop.inputs['Points']); lk.new(sm.outputs[0], iop.inputs['Instance'])
    scl = M('MULTIPLY', M('MULTIPLY', M('POWER', M('SUBTRACT', 1.0, u), 0.6), sz), rad)
    lk.new(scl, iop.inputs['Scale'])
    lk.new(iop.outputs[0], gout.inputs[0])
    return ng
def fire_emitter(name, loc, Wd, Dp, H, N_, rad, speed):
    me = bpy.data.meshes.new(name); o = bpy.data.objects.new(name, me); CP.objects.link(o)
    md = o.modifiers.new("Fire", 'NODES'); md.node_group = fire_tree(name + "_GN", Wd, Dp, H, N_, rad, speed)
    o.location = loc; o.visible_shadow = False
    return o
fire_emitter("ForgeFlames", FORGE + V(0, 0, sc["FORGE_TOP"] - 0.02), 0.45, 0.4, 0.32, 110, 0.022, 0.5)
for ng in FIRE_T:
    T = ng.nodes["T"]
    for f in (1, END_FRAME):
        T.outputs[0].default_value = f / 60.0; T.outputs[0].keyframe_insert("default_value", frame=f)
    lin_interp(ng)

# sparks (stylised impact flash on armour), steam puffs
SPARK_M = flat("Spark", (1, 0.9, 0.6), emit=(1.0, 0.85, 0.45), emit_str=25.0)
def spark(name, loc, f):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    for v in bm.verts:
        v.co *= (1.0 if (v.index % 2) else 0.35)
    o = mesh_obj(name, bm, [SPARK_M], CP); o.location = loc
    for ff, s_ in ((f - 1, 0.0), (f, 0.09), (f + 3, 0.06), (f + 7, 0.0)):
        o.scale = (s_,) * 3; o.keyframe_insert("scale", frame=ff)
    vis_only([o], [(f - 1, f + 8)])
    return o
SMOKE = flat("Steam", (0.95, 0.95, 0.95), rough=1.0, alpha=0.55)
try: SMOKE.blend_method = 'HASHED'
except Exception: pass
def steam(loc, f0, n=6):
    for i in range(n):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        o = mesh_obj("Steam%d_%d" % (f0, i), bm, [SMOKE], CP); shade_smooth(o)
        p0 = loc + V(random.uniform(-0.04, 0.04), random.uniform(-0.04, 0.04), 0.03); p1 = p0 + V(random.uniform(-0.12, 0.12), random.uniform(-0.1, 0.05), random.uniform(0.35, 0.6))
        a = f0 + i * 7
        for ff, p, s_ in ((a, p0, 0.01), (a + 20, p0.lerp(p1, 0.5), 0.06), (a + 50, p1, 0.11)):
            o.location = p; o.scale = (s_,) * 3; o.keyframe_insert("location", frame=ff); o.keyframe_insert("scale", frame=ff)
        vis_only([o], [(a, a + 50)])

# =========================================================================== SHOTS
STUMP_TOP = sc["STUMP_TOP"]
# --- S01: the punishment. Warrior kneels behind the stump, hands flat on top; soldier A beside it lifts his sword (cut before any blow)
s0, s1 = ST["S01"], SE("S01")
WK = V(0.0, 0.62, 0); WKY = 0.0
for f in (s0, s0 + 60, s1):
    b = (f - s0) / (s1 - s0)
    W.kneel(f, WK, WKY, lean=14 + 3 * math.sin(b * 6), head=(8 - 4 * b, 0))
for sd, sx in (("L", 1), ("R", -1)):
    for f in (s0, s1):
        place_hand(W.o, sd, f, V(sx * 0.11, 0.06, STUMP_TOP + 0.075), V(0, 0, -1), V(-sx * 0.25, -1, 0).normalized())
    apply_pose(W.o, sd, "relaxed", s0)
SAP = V(0.95, -0.15, 0); SAY = yaw_to(V(0, 0.3, 0) - SAP)
for f in (s0, s1):
    SA.stand(f, SAP, SAY, flex=2, head=(12, -8))
SA.hang(s0, SAP, SAY, which="L")
SA.hang(s1, SAP, SAY, which="L")
# sword: rest point-down at the side, then lifted to the shoulder, blade up and back (hand stays below the hair line)
def sword_key(c, sword, f, grip_w, tip_dir, side_dir):
    sword.matrix_world = Matrix.Translation(grip_w) @ frame_from(tip_dir, side_dir).to_4x4()
    sword.keyframe_insert("location", frame=f); sword.keyframe_insert("rotation_euler", frame=f)
RzA = Rz(SAY)
gA0 = SAP + RzA @ V(-0.30, -0.18, 0.92); tA0 = RzA @ V(0.0, -0.55, -1).normalized()
gA1 = SAP + RzA @ V(-0.26, -0.05, 1.38); tA1 = RzA @ V(0.15, 0.55, 1).normalized()
swordA.rotation_mode = 'XYZ'
for f, g, t in ((s0, gA0, tA0), (s0 + 30, gA0, tA0), (s0 + 85, gA1, tA1), (s1, gA1, tA1)):
    sword_key(SA, swordA, f, g, t, RzA @ V(1, 0, 0))
# the hand follows the sword grip (palm on the grip, fingers wrapped)
def hand_on_grip(c, sd, sword, f, palm_side):
    sc.frame_set(f); M = sword.matrix_world; g = M.translation; z = (M.to_3x3() @ V(0, 0, 1)).normalized()
    ps = (palm_side - z * palm_side.dot(z)).normalized()
    W_ = g - ps * 0.035 - z * 0.04
    c.hand_w(sd, f, W_, (z.cross(ps) if sd == "R" else ps.cross(z)).normalized(), ps,
             None)
for f, b in ((s0, 0.0), (s0 + 30, 0.0), (s0 + 85, 1.0), (s1, 1.0)):
    SA.hand_w("R", f, SAP + RzA @ V(-0.36 + 0.04 * b, -0.30 + 0.06 * b, 1.0 + 0.32 * b), RzA @ V(0, -1, -0.2 + 0.5 * b).normalized(), RzA @ V(1, 0, 0), SAP + RzA @ V(-0.6, 0.3, 1.0))
apply_pose(SA.o, "R", "wrap_grip", s0)
W.used.add("S01"); SA.used.add("S01")

# --- S02: on his knees, he lifts the bandaged forearms in front of his chest, head back (pain), soldier out of frame
s0, s1 = ST["S02"], SE("S02")
for f, b in ((s0, 0.0), (s0 + 40, 0.6), (s1, 1.0)):
    W.kneel(f, WK + V(0, 0.15, 0), WKY, lean=10 - 14 * b, head=(10 - 26 * b, 0))
    for sd, sx in (("L", 1), ("R", -1)):
        Wp = WK + V(0, 0.15, 0) + V(sx * (0.16 + 0.04 * b), -0.28 - 0.12 * b, 0.70 + 0.42 * b)
        W.hand_w(sd, f, Wp, V(-sx * 0.3, -0.3, 1).normalized(), V(0, -1, 0), WK + V(sx * 0.6, 0.6, 0.6))
SA.stand(s0, SAP + V(0.5, 0, 0), SAY); SA.stand(s1, SAP + V(0.5, 0, 0), SAY)
W.used.add("S02"); SA.used.add("S02")

# --- S03: standing, soldier points toward the village (+X), the warrior turns and walks off
s0, s1 = ST["S03"], SE("S03")
WP3 = V(-0.2, 1.1, 0); SAP3 = V(1.0, 0.0, 0); SAY3 = yaw_to(WP3 - SAP3)
W.stand(s0, WP3, 20, flex=10, head=(18, 0)); W.hang(s0, WP3, 20, out=0.16, fwd=0.05)
W.stand(s0 + 40, WP3, 20, flex=8, head=(10, -10)); W.hang(s0 + 40, WP3, 20, out=0.16, fwd=0.05)
W.stand(s0 + 62, WP3, 60, flex=6, head=(6, 10)); W.hang(s0 + 62, WP3, 60, out=0.16, fwd=0.05)
walk(W, s0 + 64, s1, WP3, WP3 + V(1.25, 0.75, 0), out=0.16, stride=0.66)
SA.stand(s0, SAP3, SAY3, head=(4, 0)); SA.stand(s1, SAP3, SAY3 - 15, head=(0, -10))
SA.hang(s0, SAP3, SAY3, which="L")
sh = SA.shoulder_w("L", SAP3, SAY3)
pt = (V(8, 4, 1.3) - sh).normalized()
for f in (s0 + 18, s1):
    SA.hand_w("L", f, sh + pt * 0.56, pt, V(0, 0, -1), sh + V(0, 0.3, -0.4))
apply_pose(SA.o, "L", "point", s0 + 18)
RzA3 = Rz(SAY3)
for f in (s0, s1):
    sword_key(SA, swordA, f, SAP3 + RzA3 @ V(-0.30, -0.18, 0.92), RzA3 @ V(0.0, -0.55, -1).normalized(), RzA3 @ V(1, 0, 0))
SA.hang(s0, SAP3, SAY3, which="R"); SA.hang(s1, SAP3, SAY3 - 15, which="R")
W.used.add("S03"); SA.used.add("S03")

# --- S04: he walks back across the meadow toward the village huts (+X), camera alongside
s0, s1 = ST["S04"], SE("S04")
p4 = walk(W, s0, s1, V(5.0, 1.0, 0), V(7.9, 1.6, 0), out=0.16, stride=0.68)
W.used.add("S04")

# --- S05: the meeting hut. He stands among the villagers; the elder speaks (open hand), the others listen
HX = 40.0
s0, s1 = ST["S05"], SE("S05")
WP5 = V(HX - 0.1, -1.25, 0); WY5 = 180.0
VPOS = {EL: (V(HX, 0.45, 0), None), VW: (V(HX - 1.05, 0.05, 0), None), M1: (V(HX + 0.45, 0.75, 0), None), M2: (V(HX + 1.15, 0.95, 0), None)}
def face(c, p, tgt): return yaw_to(tgt - p)
for f, b in ((s0, 0.0), (s0 + 70, 0.5), (s1, 1.0)):
    W.stand(f, WP5, WY5, flex=4, head=(4 * b, 0)); W.hang(f, WP5, WY5, out=0.15, fwd=0.04)
    for c, (p, _) in VPOS.items():
        y = face(c, p, WP5)
        c.stand(f, p, y, flex=3, head=(2 + 3 * math.sin(b * 3 + p.x), 4 * math.sin(b * 2 + p.y)))
        if c is not EL: c.hang(f, p, y, fwd=0.03 + 0.04 * math.sin(f * 0.05 + p.x * 3))
# elder: right hand comes up, palm up toward the warrior (telling him to surrender)
pE = VPOS[EL][0]; yE = face(EL, pE, WP5); RE = Rz(yE)
EL.hang(s0, pE, yE)
for f in (s0 + 30, s1):
    EL.hang(f, pE, yE, which="L")
    EL.hand_w("R", f, pE + RE @ V(-0.2, -0.42, 1.08), RE @ V(0.1, -1, 0.05).normalized(), V(0, 0, 1), pE + RE @ V(-0.6, 0.3, 0.9))
apply_pose(EL.o, "R", "relaxed", s0 + 30)
for c in (W, EL, VW, M1, M2): c.used.add("S05")

# --- S06: close on the warrior: he raises his bandaged right forearm and argues to keep fighting
s0, s1 = ST["S06"], SE("S06")
RW = Rz(WY5)
for f, b in ((s0, 0.0), (s0 + 45, 1.0), (s0 + 80, 0.7), (s0 + 115, 1.0), (s1, 0.85)):
    W.stand(f, WP5, WY5, flex=6 * b, head=(-4 + 8 * b, 6 * math.sin(f * 0.07)))
    W.hang(f, WP5, WY5, which="L", out=0.15, fwd=0.04)
    W.hand_w("R", f, WP5 + RW @ V(-0.2, -0.30 - 0.10 * b, 1.12 + 0.36 * b), RW @ V(0.25, -0.4, 1).normalized(), RW @ V(1, -0.3, 0).normalized(), WP5 + RW @ V(-0.55, 0.2, 0.9))
for c, (p, _) in VPOS.items():
    y = face(c, p, WP5)
    for f in (s0, s0 + 50, s0 + 100, s1):
        c.stand(f, p, y, head=(4 * math.sin(f * 0.06 + p.x), 6 * math.sin(f * 0.04 + p.y)), side=2 * math.sin(f * 0.03 + p.x)); c.hang(f, p, y, fwd=0.03 + 0.04 * math.sin(f * 0.05 + p.x * 3))
for c in (W, EL, VW, M1, M2): c.used.add("S06")

# --- S07: the villagers raise their fists and agree (fists at shoulder height, below the hair line)
s0, s1 = ST["S07"], SE("S07")
VPOS7 = {EL: (V(HX - 0.05, 0.5, 0), None), VW: (V(HX - 0.75, 0.15, 0), None), M1: (V(HX + 0.55, 0.25, 0), None), M2: (V(HX - 0.42, 1.1, 0), None)}
WP7 = V(HX + 1.6, -1.6, 0)
for c, (p, _) in VPOS7.items():
    y = face(c, p, WP7); R3 = Rz(y)
    c.stand(s0, p, y, head=(0, 0)); c.hang(s0, p, y)
    c.stand(s0 + 30, p, y, flex=-3, head=(-6, 0)); c.stand(s1, p, y, flex=2, head=(6, 0))
    c.hang(s0 + 30, p, y, which="L"); c.hang(s1, p, y, which="L")
    sh = c.shoulder_w("R", p, y)
    for f, h in ((s0 + 12, 0.0), (s0 + 34, 1.0), (s0 + 60, 0.85), (s0 + 84, 1.0), (s1, 0.9)):
        Wf = sh + R3 @ V(-0.08, -0.22, -0.05 + 0.25 * h)
        c.hand_w("R", f, Wf, R3 @ V(0, -0.3, 1).normalized(), R3 @ V(1, 0, 0) * -1, sh + R3 @ V(-0.35, 0.2, -0.35))
    apply_pose(c.o, "R", "power_fist", s0 + 34)
WY7 = yaw_to(V(HX, 0.4, 0) - WP7)
W.stand(s0, WP7, WY7, head=(6, 0)); W.stand(s1, WP7, WY7, head=(-4, 0))
W.hang(s0, WP7, WY7, out=0.15, fwd=0.04); W.hang(s1, WP7, WY7, out=0.15, fwd=0.04)
for c in (W, EL, VW, M1, M2): c.used.add("S07")

# --- S08: the forge: an iron plate glowing in the coals (camera only, flames keyed)
# --- S09: he presses the stump onto the glowing plate on the anvil; steam; pain
s0, s1 = ST["S09"], SE("S09")
WP9 = V(ANV.x + 0.02 - 0.2, ANV.y - 0.04 - 0.5, 0); WY9 = 180.0; R9 = Rz(WY9)
con = plate9.location + V(0, 0, 0.012)
for f, b, lean in ((s0, 0.0, 10), (s0 + 40, 0.6, 22), (s0 + 60, 1.0, 30), (s1, 1.0, 28)):
    W.stand(f, WP9, WY9, flex=lean, head=(4 - 30 * b, 8 * b), crouch=0.02 + 0.13 * b)
    W.hang(f, WP9, WY9, which="L", out=0.16, fwd=0.04)
c9, ax9, _ = CUT["R"]
for f, h in ((s0, 0.28), (s0 + 40, 0.10), (s0 + 60, 0.0), (s1, 0.0)):
    # stump end (bandage tip) lands on the plate: the wrist point sits ~3 cm above the contact
    W.hand_w("R", f, con + V(0, 0, 0.035 + h) + R9 @ V(0, 0.02, 0), V(0, 0.15, -1).normalized(), R9 @ V(1, 0, 0), WP9 + R9 @ V(-0.6, 0.0, 1.0))
# (steam dropped: the spheres read as a solid white ball at preview size; the glow carries the beat)
W.used.add("S09")

# --- S10: close-up of two knives and leather straps laid on the table (camera only)
TB = Vector(sc["TABLE"])
for i, (dx, rot) in enumerate(((-0.12, 8), (0.12, -6))):
    k = knife_src.copy(); k.data = knife_src.data; CP.objects.link(k); k.name = "TableKnife%d" % i
    k.hide_render = False; k.hide_viewport = False
    k.matrix_world = Matrix.Translation(TB + V(dx, -0.12, 0.012)) @ Matrix.Rotation(R_(rot), 4, 'Z') @ Matrix.Rotation(R_(-90), 4, 'X') @ Matrix.Rotation(R_(90), 4, 'Z')
    vis_only([k], [(ST["S10"], SE("S10"))])
    bm = bmesh.new()
    for j in range(3):
        bmesh.ops.create_circle(bm, segments=28, radius=0.05 - 0.008 * j)
    o = mesh_obj("StrapCoil%d" % i, bm, [LEATHER], CP); o.location = TB + V(dx * 1.6, 0.14, 0.006)
    so = o.modifiers.new("Skin", 'SKIN')
    for sv in o.data.skin_vertices[0].data: sv.radius = (0.009, 0.004)
    vis_only([o], [(ST["S10"], SE("S10"))])

# --- S11: the knives are strapped on; he lifts both forearms and looks at the blades; a villager nods beside him
s0, s1 = ST["S11"], SE("S11")
WP11 = V(HX + 0.15, 0.35, 0); WY11 = 0.0; R11 = Rz(WY11)
for f, b in ((s0, 0.0), (s0 + 50, 1.0), (s0 + 100, 0.8), (s1, 1.0)):
    W.stand(f, WP11, WY11, flex=4, head=(18 * b, 10 * math.sin(f * 0.04)))
    for sd, sx in (("L", 1), ("R", -1)):
        W.hand_w(sd, f, WP11 + R11 @ V(sx * (0.24 + 0.03 * b), -0.44 - 0.04 * b, 1.24 + 0.2 * b),
                 R11 @ V(-sx * 0.2, -0.6, 0.8 * b + 0.1).normalized(), R11 @ V(-sx, 0, 0), WP11 + R11 @ V(sx * 0.6, 0.3, 0.9))
pM2 = V(HX + 1.0, 0.75, 0); yM2 = face(M2, pM2, WP11)
for f, b in ((s0, 0), (s0 + 60, 1), (s0 + 100, 0), (s1, 1)):
    M2.stand(f, pM2, yM2, head=(10 * b, 0)); M2.hang(f, pM2, yM2)
vis_only(KNIVES, [(ST["S11"], END_FRAME)])
for c in (W, M2): c.used.add("S11")

# --- battlefield (-40, 0)
BX = -40.0
# S12: he strides toward the camera with the blades, two villagers behind him
s0, s1 = ST["S12"], SE("S12")
walk(W, s0, s1, V(BX - 1.0, 4.4, 0), V(BX - 1.0, 1.9, 0), out=0.2, stride=0.72, swing=0.14)
walk(M1, s0, s1, V(BX - 2.2, 6.0, 0), V(BX - 2.2, 3.6, 0), stride=0.72)
walk(M2, s0 + 10, s1, V(BX + 0.3, 6.4, 0), V(BX + 0.3, 4.0, 0), stride=0.72)
for c in (W, M1, M2): c.used.add("S12")

# S13: he slashes a soldier; spark on the cuirass; the soldier staggers back (no wound)
s0, s1 = ST["S13"], SE("S13")
WP13 = V(BX, 1.2, 0); WY13 = 0.0; R13 = Rz(WY13)
SBP = V(BX + 0.05, -0.18, 0); SBY = 180.0
FH = s0 + 52
for f, b in ((s0, 0.0), (s0 + 30, 0.0), (FH - 6, 0.6), (FH, 1.0), (FH + 14, 1.0), (s1, 0.8)):
    W.stand(f, WP13 + V(0, -0.15 * b, 0), WY13 + 20 * b, flex=8 + 8 * b, head=(6, 0), twist=-25 + 45 * b)
# right forearm: wind up to the right shoulder, sweep across in front of the soldier's chest (15 cm clear), follow through left
sw = [(s0, V(-0.30, -0.36, 1.18)), (s0 + 30, V(-0.62, -0.48, 1.38)), (FH - 6, V(-0.42, -0.58, 1.36)), (FH, V(-0.02, -0.60, 1.33)),
      (FH + 10, V(0.02, -0.62, 1.25)), (s1, V(-0.14, -0.60, 1.2))]
for f, p in sw:
    W.hand_w("R", f, WP13 + R13 @ p, R13 @ V(-0.2, -1, 0.15).normalized(), R13 @ V(0, 0, -1), WP13 + R13 @ V(-0.6, 0.2, 1.0))
for f in (s0, s1): W.hand_w("L", f, WP13 + R13 @ V(0.40, -0.40, 1.15), R13 @ V(0.2, -1, 0.3).normalized(), R13 @ V(1, 0, 0), WP13 + R13 @ V(0.6, 0.3, 0.9))
for f, back, lean in ((s0, 0.0, 0), (FH, 0.0, 0), (FH + 8, 0.2, -12), (FH + 30, 0.4, -6), (s1, 0.45, 4)):
    SB.stand(f, SBP + V(0, -back, 0), SBY + 12 * (back > 0), flex=lean, head=(lean * 0.5, 0))
    SB.hang(f, SBP + V(0, -back, 0), SBY, swing=(0.15 * (back > 0), 0.25 * (back > 0)), out=0.13 + 0.1 * (back > 0), fwd=0.08)
spark("SparkS13", SBP + V(0, 0.24, 1.3), FH)
for c in (W, SB): c.used.add("S13")

# S14: the general's second-in-command (brass helmet) comes at him with a sword; he ducks inside and cuts; spark; the officer reels
s0, s1 = ST["S14"], SE("S14")
WP14 = V(BX - 3.0, 0.78, 0); WY14 = 0.0; R14 = Rz(WY14)
SCP0 = V(BX - 3.0, -1.7, 0); SCP1 = V(BX - 3.0, -0.75, 0); SCY = 180.0; RS = Rz(SCY)
FH2 = s0 + 100
walk(SC2, s0, s0 + 60, SCP0, SCP1, yaw=SCY, stride=0.7, arms="L")
for f, back, lean in ((s0 + 60, 0, 4), (FH2, 0, 6), (FH2 + 10, 0.3, -14), (FH2 + 40, 0.65, -4), (s1, 0.8, 6)):
    SC2.stand(f, SCP1 + V(0, -back, 0), SCY, flex=lean, head=(lean * 0.6, 0))
    SC2.hang(f, SCP1 + V(0, -back, 0), SCY, which="L", swing=(0.2 * (back > 0), 0))
# sword raised at shoulder height, blade up and back, then a cut that stops short (beside him, never through him)
for f, g, t in ((s0, V(-0.28, -0.12, 1.0), V(0, -0.4, 1)), (s0 + 60, V(-0.28, -0.05, 1.42), V(0.1, 0.6, 1)),
                (FH2 - 14, V(-0.30, -0.02, 1.48), V(0.1, 0.7, 1)), (FH2, V(-0.32, -0.30, 1.30), V(-0.1, -0.4, 1)),
                (FH2 + 10, V(-0.34, -0.12, 1.15), V(-0.4, -0.1, 1)), (s1, V(-0.32, -0.1, 1.0), V(-0.3, -0.2, 1))):
    base = SCP1 if f >= s0 + 60 else SCP0.lerp(SCP1, (f - s0) / 60)
    if f > FH2: base = SCP1 + V(0, -0.3 * min(1, (f - FH2) / 10) - 0.35 * max(0, min(1, (f - FH2 - 10) / 30)), 0)
    sword_key(SC2, swordB, f, base + RS @ g, (RS @ t).normalized(), RS @ V(1, 0, 0))
for f, p_ in ((s0, V(-0.48, -0.30, 0.98)), (s0 + 60, V(-0.52, -0.34, 1.0)), (FH2 - 14, V(-0.52, -0.32, 1.0)), (FH2, V(-0.66, -0.30, 0.92)), (FH2 + 10, V(-0.62, -0.26, 0.92)), (s1, V(-0.50, -0.32, 0.94))):
    base = SCP1 if f >= s0 + 60 else SCP0.lerp(SCP1, (f - s0) / 60)
    if f > FH2: base = SCP1 + V(0, -0.3 * min(1, (f - FH2) / 10) - 0.35 * max(0, min(1, (f - FH2 - 10) / 30)), 0)
    SC2.hand_w("R", f, base + RS @ p_, RS @ V(0, -1, -0.25).normalized(), RS @ V(1, 0, 0), base + RS @ V(-0.6, 0.3, 1.0))
apply_pose(SC2.o, "R", "wrap_grip", s0)
for f, b, tw in ((s0, 0.0, 0), (s0 + 60, 0.2, -10), (FH2 - 8, 0.6, -30), (FH2, 1.0, 20), (FH2 + 16, 1.0, 25), (s1, 0.8, 15)):
    W.stand(f, WP14 + V(0.25 * b, -0.08 * b, 0), WY14 - 10 * b, flex=4 + 3 * b, head=(2, 0), twist=tw, crouch=0.02 + 0.04 * b)
for f, p in ((s0, V(-0.32, -0.45, 1.18)), (FH2 - 8, V(-0.62, -0.52, 1.36)), (FH2, V(0.02, -0.76, 1.40)), (FH2 + 12, V(0.0, -0.76, 1.25)), (s1, V(-0.14, -0.70, 1.2))):
    W.hand_w("R", f, WP14 + R14 @ p, R14 @ V(-0.2, -1, 0.15).normalized(), R14 @ V(0, 0, -1), WP14 + R14 @ V(-0.6, 0.2, 1.0))
for f in (s0, s1): W.hand_w("L", f, WP14 + R14 @ V(0.52, -0.66, 1.2), R14 @ V(0.2, -1, 0.3).normalized(), R14 @ V(1, 0, 0), WP14 + R14 @ V(0.6, 0.3, 0.9))
spark("SparkS14", SCP1 + V(0.08, 0.22, 1.25), FH2)
for c in (W, SC2): c.used.add("S14")

# S15: the invaders' flag against the dusk sky (camera only)
# S16: the invading army marches over the meadow (one marcher action, copied in formation); the warrior faces them
s0, s1 = ST["S16"], SE("S16")
ARMY0 = V(BX + 2.0, -9.0, 0); ARMY1 = V(BX + 2.0, -6.4, 0)
walk(SC, s0, s1, ARMY0, ARMY1, yaw=180.0, stride=0.7, arms="L", swing=0.15)
for f in sorted(set(list(range(s0, s1 + 1, 6)) + [s1])):
    u = (f - s0) / (s1 - s0); p = ARMY0.lerp(ARMY1, u)
    SC.hand_w("R", f, p + Rz(180) @ V(-0.42, -0.26, 1.0), Rz(180) @ V(0, -1, -0.15).normalized(), Rz(180) @ V(1, 0, 0), p + Rz(180) @ V(-0.6, 0.3, 0.9))
WP16 = V(BX + 2.2, -2.0, 0)
for f, b in ((s0, 0), (s0 + 60, 1), (s0 + 110, 0), (s1, 1)):
    W.stand(f, WP16, 0, flex=6, head=(-4 * b, 6 * b), crouch=0.06)
    for sd, sx in (("L", 1), ("R", -1)):
        W.hand_w(sd, f, WP16 + V(sx * 0.3, -0.32, 1.2 + 0.05 * b), V(-sx * 0.2, -1, 0.35).normalized(), V(-sx, 0, 0), WP16 + V(sx * 0.6, 0.3, 0.9))
for c in (W, SC): c.used.add("S16")

# S17: surrounded by guards with spears; he turns, slashes once, then stands defiant to the end (push in on his face)
s0, s1 = ST["S17"], SE("S17")
RC = V(BX + 6.0, 4.0, 0)
WP17 = RC; WY17 = 0.0
GUARD_LOCAL = V(RC.x + 1.0, RC.y + 1.9, 0); GY = 0.0      # SoldierB master guard stands north of the warrior, facing him (south)
for f, b in ((s0, 0), (s0 + 60, 0.5), (s1, 1)):
    SB.stand(f, GUARD_LOCAL, GY, flex=4, head=(-2, 0), stance=1.2, crouch=0.05)
    SB.hand_w("R", f, GUARD_LOCAL + Rz(GY) @ V(-0.36, -0.24, 1.0), Rz(GY) @ V(0, -1, -0.15).normalized(), Rz(GY) @ V(1, 0, 0), GUARD_LOCAL + Rz(GY) @ V(-0.6, 0.3, 0.9))
    SB.hang(f, GUARD_LOCAL, GY, which="L")
FH3 = s0 + 70
for f, yaw, b, tw in ((s0, -30, 0, 0), (s0 + 40, -10, 0.3, -25), (FH3, 15, 1.0, 25), (FH3 + 20, 20, 0.9, 20), (s0 + 150, 0, 0.5, 0), (s0 + 215, -12, 0.45, -8), (s0 + 280, 10, 0.5, 6), (s1, -4, 0.4, 0)):
    W.stand(f, WP17, yaw, flex=8 + 8 * b, head=(-8 + 6 * math.sin(f * 0.03), 9 * math.sin(f * 0.021)), twist=tw, crouch=0.04 + 0.05 * b)
    R3 = Rz(yaw)
    rp = V(-0.42, -0.42, 1.38) if f < FH3 else (V(0.0, -0.74, 1.33) if f == FH3 else V(-0.30, -0.48, 1.25))
    W.hand_w("R", f, WP17 + R3 @ rp, R3 @ V(-0.2, -1, 0.3).normalized(), R3 @ V(0, 0, -1), WP17 + R3 @ V(-0.6, 0.2, 1.0))
    W.hand_w("L", f, WP17 + R3 @ V(0.32, -0.46, 1.25), R3 @ V(0.2, -1, 0.35).normalized(), R3 @ V(1, 0, 0), WP17 + R3 @ V(0.6, 0.3, 0.9))
for c in (W, SB): c.used.add("S17")

# --- spears: Child Of the wrist at a frame where the hand holds the shaft upright
def spear_grip(c, sp, f, d, n):
    """shaft vertical through the closed fist (palm faces the body, fingers forward): wrap grip + Child Of the wrist"""
    sc.frame_set(f)
    wr = c.world_bone("wrist.R", f).translation
    d = Vector(d).normalized(); n = Vector(n).normalized()
    pc = wr + d * 0.062 + n * 0.032
    sp.matrix_world = Matrix.Translation(pc) @ frame_from(-n * 0.32 + d * 0.10 + V(0, 0, 1), d).to_4x4()
    apply_pose(c.o, "R", "wrap_grip", f)
    bpy.context.view_layer.update()
    child_of_now(sp, c.o, "wrist.R", f)
spear_grip(SC, spear, ST["S16"] + 20, Rz(180) @ V(0, -1, -0.15), Rz(180) @ V(1, 0, 0))
spear_grip(SB, spearB, ST["S17"] + 20, Rz(GY) @ V(0, -1, -0.15), Rz(GY) @ V(1, 0, 0))
vis_only([spear], [(ST["S16"], END_FRAME)]); vis_only([spearB], [(ST["S17"], END_FRAME)])
# the swords: Child Of is not used (keyed transforms + the hand follows the grip); visibility per shot
for sw_, c_, f_ in ((swordA, SA, ST["S01"]), (swordB, SC2, ST["S14"])):
    if sw_.animation_data: sw_.animation_data_clear()
    sc.frame_set(f_)
    M_ = c_.world_bone("wrist.R", f_); wr_ = M_.translation
    d_ = (c_.world_bone("finger3-1.R", f_).translation - wr_).normalized()
    a_ = (c_.world_bone("finger2-1.R", f_).translation - c_.world_bone("finger5-1.R", f_).translation).normalized()
    n_ = a_.cross(d_).normalized()
    pc_ = wr_ + d_ * 0.08 + n_ * 0.042
    sw_.matrix_world = Matrix.Translation(pc_) @ frame_from(a_, d_).to_4x4()
    bpy.context.view_layer.update()
    pbI = c_.o.pose.bones["IK_hand.R"]; keep = pbI.matrix.copy()
    rep_ = grip_object(c_.o, "R", f_, sw_, pc_, n_, finger_dir=d_, finger_radius=0.013)   # fingers close onto the hilt
    print("GRIP", sw_.name, rep_)
    child_of_now(sw_, c_.o, "wrist.R", f_)                     # sword rides with the gripping hand
    sc.frame_set(f_); pbI.matrix = keep; bpy.context.view_layer.update()
    pbI.keyframe_insert("location", frame=f_, group=pbI.name); pbI.keyframe_insert("rotation_quaternion", frame=f_, group=pbI.name)
vis_only([swordA], [(ST["S01"], SE("S01"))]); vis_only([swordB], [(ST["S14"], SE("S14"))])

# --- copies: the marching army (SoldierC) and the guard ring (SoldierB); each copy shares the master's action
COPY_C = coll("Copies")
def copy_char(c, idx, T, shown):
    rig = c.o.copy(); rig.data = c.o.data; COPY_C.objects.link(rig); rig.name = "%s_cp%02d" % (c.o.name, idx)
    rig.matrix_world = T @ c.o.matrix_world
    objs = [rig]
    for ch in list(c.o.children):
        if ch.type != 'MESH': continue
        n = ch.copy(); COPY_C.objects.link(n); n.name = "%s_cp%02d" % (ch.name, idx); n.parent = rig
        for m in n.modifiers:
            if m.type == 'ARMATURE': m.object = rig
        n.animation_data_clear(); objs.append(n)
    sp = bpy.data.objects.get("SpearC" if c is SC else "SpearB")
    s2 = sp.copy(); COPY_C.objects.link(s2); s2.name = "%s_spear%02d" % (c.o.name, idx)
    for cn in s2.constraints:
        if cn.type == 'CHILD_OF': cn.target = rig
    s2.animation_data_clear(); objs.append(s2)
    vis_only(objs[1:], shown)
    return objs
idx = 0
for row in range(5):
    for col in range(6):
        if row == 0 and col == 3: continue
        off = V((col - 3) * 1.2 + 0.35 * (row % 2), -row * 1.45 - 0.25 * (col % 2), 0)
        copy_char(SC, idx, Matrix.Translation(off), [(ST["S16"], END_FRAME)]); idx += 1
# master SC is the front-centre marcher; in S17 the army stands behind the ring (the master keeps its S16 end pose)
gi = 0
for a_deg in (-48, -6, 36, 144, 186, 228):
    a = math.radians(a_deg)
    tgt = RC + V(2.1 * math.cos(a), 2.1 * math.sin(a), 0)
    yaw = yaw_to(RC - tgt)
    T = Matrix.Translation(tgt) @ Rz(yaw - GY).to_4x4() @ Matrix.Translation(-GUARD_LOCAL)
    copy_char(SB, gi, T, [(ST["S17"], END_FRAME)]); gi += 1

# soldier A's and B's helmets & plates are bone children: fine. Park everyone in the shots they are not in.
SHOTS = [s for s, _ in SHOT_LEN]
for c in CAST:
    for s in SHOTS:
        if s in c.used: continue
        if c is SC and s == "S17": continue      # marcher master stays in the army behind the ring
        if c is SB and s in ("S17",): continue
        park(c, ST[s]); park(c, SE(s))
# SC in S17: hold the S16 end pose shifted forward to stand behind the ring
p = ARMY1
SC.stand(ST["S17"], p, 180.0); SC.stand(SE("S17"), p, 180.0)
SC.hang(ST["S17"], p, 180.0, which="L"); SC.hang(SE("S17"), p, 180.0, which="L")
SC.hand_w("R", ST["S17"], p + Rz(180) @ V(-0.42, -0.26, 1.0), Rz(180) @ V(0, -1, -0.15).normalized(), Rz(180) @ V(1, 0, 0), p + Rz(180) @ V(-0.6, 0.3, 0.9))
SC.hand_w("R", SE("S17"), p + Rz(180) @ V(-0.42, -0.26, 1.0), Rz(180) @ V(0, -1, -0.15).normalized(), Rz(180) @ V(1, 0, 0), p + Rz(180) @ V(-0.6, 0.3, 0.9))
# swords constant between keys outside their shots
const_interp(swordA) if False else None

for c in (EL, VW, M1, M2):
    for sd in "LR": apply_pose(c.o, sd, "relaxed", SE("S07") + 1)
for sd in "LR": apply_pose(SB.o, sd, "relaxed", SE("S13"))
# =========================================================================== world dusk + flag wave + lights per shot
w = sc.world; DV = w.node_tree.nodes["DUSKV"]
sun = bpy.data.objects["Sun"].data
DUSK_SHOTS = {"S15", "S16", "S17"}
for s in SHOTS:
    d = 1.0 if s in DUSK_SHOTS else 0.0
    DV.outputs[0].default_value = d; DV.outputs[0].keyframe_insert("default_value", frame=ST[s])
    sun.color = (1.0, 0.72, 0.62) if d else (1.0, 0.96, 0.9); sun.energy = 2.4 if d else 3.2
    sun.keyframe_insert("color", frame=ST[s]); sun.keyframe_insert("energy", frame=ST[s])
const_interp(w.node_tree); const_interp(sun)
so = bpy.data.objects["Sun"]
for s in SHOTS:
    so.rotation_euler = (R_(74), 0, R_(-60)) if s in DUSK_SHOTS else (R_(48), 0, R_(-35))
    so.keyframe_insert("rotation_euler", frame=ST[s])
const_interp(so)
flag = bpy.data.objects["Flag"]; wv = flag.modifiers["Wave"]; wv.speed = 0.25
for f in (1, END_FRAME):
    wv.time_offset = -f * 0.0; wv.keyframe_insert("time_offset", frame=f)
vis_only([bpy.data.objects['Flag'], bpy.data.objects['FlagPole']], [(ST['S15'], END_FRAME)])
vis_only([bpy.data.objects['Logo_Crate'], bpy.data.objects['Logo_Crate2']], [(ST['S07'], SE('S07'))])   # logo only where the crate is whole and flat-on
hz = bpy.data.materials.new("Haze"); hn, hl_ = nodes_of(hz); hn.clear()
ho_ = hn.new('ShaderNodeOutputMaterial'); pv = hn.new('ShaderNodeVolumePrincipled'); pv.inputs['Density'].default_value = 0.012
pv.inputs['Color'].default_value = (1.0, 0.85, 0.85, 1); hl_.new(pv.outputs[0], ho_.inputs['Volume'])
bm = bmesh.new(); add_box(bm, V(BX - 18, -45, -0.5), V(BX + 18, -2.0, 14)); hzo = mesh_obj("Haze", bm, [hz], CP)
vis_only([hzo], [(ST['S16'], SE('S16'))])
# hut fill under the roof
hl = bpy.data.lights.new("HutFill", 'AREA'); hl.size = 5.0; hl.energy = 600; hl.color = (0.94, 0.96, 1.0)
ho = bpy.data.objects.new("HutFill", hl); CP.objects.link(ho); ho.location = (HX, 0, 2.6)

# =========================================================================== cameras (one per shot, hard cuts) + catchlights
CAMS = coll("Cameras")
def camera(shot, keys, lens=35, fstop=None):
    cd = bpy.data.cameras.new("CAM_" + shot); cd.lens = lens; cd.clip_start = 0.05; cd.clip_end = 400
    cd.sensor_fit = 'AUTO'; cd.dof.use_dof = False
    co = bpy.data.objects.new("CAM_" + shot, cd); CAMS.objects.link(co)
    tg = bpy.data.objects.new("CAMT_" + shot, None); CAMS.objects.link(tg)
    c = co.constraints.new('TRACK_TO'); c.target = tg; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
    s0, s1 = ST[shot], SE(shot)
    for off, loc, tgt in keys:
        f = s0 + off if off >= 0 else s1 + 1 + off
        co.location = loc; co.keyframe_insert("location", frame=f)
        tg.location = tgt; tg.keyframe_insert("location", frame=f)
    m = sc.timeline_markers.new(shot, frame=s0); m.camera = co
    # small camera-side catchlight (glossy only), on during this shot
    L_ = bpy.data.lights.new("Catch_" + shot, 'POINT'); L_.shadow_soft_size = 0.05; L_.color = (1, 1, 1)
    lo = bpy.data.objects.new("Catch_" + shot, L_); CAMS.objects.link(lo); lo.parent = co; lo.location = (0.08, 0.1, 0)
    lo.visible_diffuse = False; lo.visible_transmission = False; lo.visible_volume_scatter = False
    for f, e in ((1, 0.0), (s0, 4.0), (s1 + 1, 0.0)):
        L_.energy = e; L_.keyframe_insert("energy", frame=f)
    const_interp(L_)
    return co

def head_at(c, f): return c.world_bone("head", f).translation + V(0, 0, 0.08 * c.s / 1.0 * 0 + 0.08)
# S01 wide low front-left: stump, kneeling warrior, soldier lifting the sword
camera("S01", [(0, V(-1.55, -2.7, 0.95), V(0.35, 0.25, 0.85)), (-1, V(-1.3, -2.35, 0.98), V(0.35, 0.25, 0.95))], lens=28)
h2 = head_at(W, ST["S02"] + 60)
camera("S02", [(0, h2 + V(0.35, -1.55, -0.45), h2 + V(0, 0, -0.25)), (-1, h2 + V(0.3, -1.35, -0.42), h2 + V(0, 0, -0.18))], lens=32)
camera("S03", [(0, V(-2.3, -0.2, 1.5), V(0.4, 0.6, 1.3)), (-1, V(-2.0, 0.2, 1.5), V(0.8, 1.0, 1.3))], lens=30)
camera("S04", [(0, V(7.6, -1.4, 1.5), p4(ST["S04"]) + V(0, 0, 1.45)), (-1, V(9.6, -0.6, 1.5), p4(SE("S04")) + V(0, 0, 1.45))], lens=32)
camera("S05", [(0, V(HX + 2.7, -1.6, 1.55), V(HX - 0.05, -0.2, 1.35)), (-1, V(HX + 2.5, -1.45, 1.55), V(HX - 0.05, -0.2, 1.38))], lens=22)
h6 = head_at(W, ST["S06"] + 40)
camera("S06", [(0, h6 + V(0.55, 1.5, -0.12), h6 + V(0, 0, -0.22)), (-1, h6 + V(0.42, 1.25, -0.1), h6 + V(0, 0, -0.18))], lens=35)
camera("S07", [(0, V(HX - 0.1, -3.6, 1.5), V(HX - 0.25, 0.3, 1.4)), (-1, V(HX - 0.1, -3.3, 1.5), V(HX - 0.25, 0.3, 1.45))], lens=20)
FT = sc["FORGE_TOP"]
camera("S08", [(0, FORGE + V(-0.3, -1.6, FT + 0.8), FORGE + V(0, 0, FT)), (-1, FORGE + V(-0.2, -1.2, FT + 0.62), FORGE + V(0, 0, FT))], lens=40)
h9 = head_at(W, ST["S09"] + 70)
camera("S09", [(0, WP9 + V(1.45, 0.45, 1.5), h9 * 0.58 + con * 0.42), (-1, WP9 + V(1.3, 0.42, 1.48), h9 * 0.6 + con * 0.4)], lens=30)
camera("S10", [(0, TB + V(0.05, -0.75, 0.55), TB + V(0, 0, 0.02)), (-1, TB + V(0.03, -0.5, 0.4), TB + V(0, 0, 0.02))], lens=40)
h11 = head_at(W, ST["S11"] + 60)
camera("S11", [(0, WP11 + V(-0.35, -2.1, 1.45), WP11 + V(0, 0, 1.3)), (-1, WP11 + V(-0.25, -1.8, 1.45), WP11 + V(0, 0, 1.35))], lens=30)
camera("S12", [(0, V(BX - 0.6, 0.2, 1.1), V(BX - 1.0, 4.4, 1.35)), (-1, V(BX - 0.6, -0.9, 1.15), V(BX - 1.0, 2.0, 1.4))], lens=28)
camera("S13", [(0, V(BX + 2.75, 0.55, 1.35), V(BX, 0.5, 1.2)), (-1, V(BX + 2.6, 0.4, 1.32), V(BX, 0.4, 1.2))], lens=24)
camera("S14", [(0, V(BX + 0.3, -0.5, 1.45), V(BX - 3.0, -0.55, 1.2)), (-1, V(BX + 0.1, -0.45, 1.42), V(BX - 3.0, -0.5, 1.22))], lens=22)
FLP = Vector(sc["FLAG"])
camera("S15", [(0, FLP + V(2.6, -6.5, -4.2), FLP + V(0.6, 0, -1.2)), (-1, FLP + V(2.2, -6.0, -4.0), FLP + V(0.8, 0, -0.5))], lens=30)
camera("S16", [(0, V(BX + 4.4, -3.0, 1.62), V(BX + 1.6, -7.6, 1.45)), (-1, V(BX + 4.3, -3.3, 1.62), V(BX + 1.6, -7.4, 1.5))], lens=28)
h17 = head_at(W, ST["S17"] + 150)
camera("S17", [(0, RC + V(0.6, -3.6, 1.7), RC + V(0, 0, 1.2)), (150, RC + V(0.35, -1.6, 1.6), RC + V(0, 0, 1.45)), (-1, RC + V(0.25, -1.1, 1.62), RC + V(0, 0, 1.55))], lens=30)
sc.camera = bpy.data.objects["CAM_S01"]

# =========================================================================== look
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'
sc.render.use_motion_blur = False
sc.render.fps = 60; sc.render.resolution_x = 1080; sc.render.resolution_y = 1920; sc.render.resolution_percentage = 100
sc["SHOTS_JSON"] = json.dumps([[s, ST[s], SE(s)] for s, _ in SHOT_LEN])
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ANIM_DONE frames", sc.frame_start, sc.frame_end)
