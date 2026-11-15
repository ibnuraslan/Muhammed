"""B04 animation, props, cameras and look. Every action is keyed at an offset from its shot's start (timing.py), 1x speed.
blender -b sets.blend --python 03_anim.py -- <out.blend>"""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion
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
BX0, BX1, BY0, BY1, BZ = sc["BOX"]
CUR_S = [1.0]

def ground_w(x, y):
    if BX0 < x < BX1 and BY0 < y < BY1: return BZ
    if 92 < x < 108 and -45 < y < 45 and (x < 93 or x > 107): return 0.15
    return 0.0
def ground_z(x, y):            # anim_lib calls this with armature-space xy of the character being keyed
    s = CUR_S[0]; return ground_w(x * s, y * s) / s

_kf0 = Human.key_foot
def _kf(self, s, f, xy, yaw, lift=0.0, pitch=0.0):     # MPFB shoe soles dip ~2 cm below the ankle-derived floor line
    _kf0(self, s, f, xy, yaw, lift + 0.035 / CUR_S[0], pitch)
Human.key_foot = _kf
_kr0 = Human.key_root
def _kr(self, f, pos, yaw=0.0, flex=0.0, side=0.0):    # hips rise with the lifted feet (no knee bend from the lift)
    _kr0(self, f, Vector((pos.x, pos.y, pos.z + 0.035 / CUR_S[0])), yaw=yaw, flex=flex, side=side)
Human.key_root = _kr

def yaw_to(d):
    return math.degrees(math.atan2(d.x, -d.y))

class Char:
    def __init__(self, name, height_scale):
        self.o = bpy.data.objects[name]; self.s = height_scale
        self.o.scale = (height_scale,) * 3; self.o.location = (0, 0, 0)
        self.R = Rig(self.o); self.H = Human(self.R)
        for pb in self.o.pose.bones: pb.rotation_mode = 'QUATERNION'
    def use(self): CUR_S[0] = self.s; return self
    def a(self, v): return Vector(v) / self.s                     # world -> armature space
    def root(self, f, pos_w, yaw=0.0, flex=0.0, side=0.0, dz=0.0):
        self.use(); p = self.a(pos_w); p.z = self.H.root_head.z + (ground_w(pos_w[0], pos_w[1]) + dz) / self.s if len(pos_w) == 2 or pos_w[2] is None else p.z
        self.H.key_root(f, p, yaw=yaw, flex=flex, side=side)
    def foot(self, s, f, xy_w, yaw, lift=0.0, pitch=0.0):
        self.use(); self.H.key_foot(s, f, self.a((xy_w[0], xy_w[1], 0)).to_2d(), yaw, lift / self.s, pitch)
    def stand(self, f, pos_w, yaw, crouch=0.02, flex=3.0, head=(0.0, 0.0), twist=0.0, stance=1.0):
        """both feet planted under the hips, root at standing height"""
        self.use(); g = ground_w(*pos_w[:2]); P = self.a((pos_w[0], pos_w[1], 0))
        self.H.key_root(f, Vector((P.x, P.y, g / self.s + self.H.root_head.z - crouch / self.s)), yaw=yaw, flex=flex * 0.5)
        self.H.key_spine(f, flex=flex, twist=twist, head=head)
        for sd in "LR":
            xy = self.H.foot_xy(sd, Vector((P.x, P.y, 0)), yaw)
            if stance != 1.0:
                c = Vector((P.x, P.y)); xy = c + (xy - c) * stance
            self.H.key_foot(sd, f, xy, yaw)
    def world_bone(self, n, f=None):
        if f is not None: sc.frame_set(int(f))
        return self.o.matrix_world @ self.o.pose.bones[n].matrix
    def hand_w(self, s, f, W, d, n, pole_w=None):
        """IK hand: wrist at world W, fingers along d, palm normal n (world)"""
        self.use(); R3 = self.o.matrix_world.to_3x3().normalized().inverted()
        self.H.key_hand(s, f, self.a(W), R3 @ Vector(d), R3 @ Vector(n), None if pole_w is None else self.a(pole_w))
    def hang(self, f, pos_w, yaw, swing=(0.0, 0.0), out=0.11):
        """relaxed hanging arms beside the thighs (slight elbow bend); swing = forward offset (m) per side L,R"""
        Rz = Matrix.Rotation(R_(yaw), 3, 'Z'); g = ground_w(*pos_w[:2])
        for i, sd in enumerate("LR"):
            sx = 1 if sd == "L" else -1
            sh = self.o.data.bones["upperarm01." + sd].head_local * self.s
            W = V(pos_w[0], pos_w[1], g) + Rz @ V(sx * (abs(sh.x) + out * self.s / 1.2), -0.06 - swing[i], sh.z - 0.56 * self.s)
            d = Rz @ V(0, -0.15 - swing[i] * 0.6, -1).normalized(); n = Rz @ V(-sx, 0, 0)
            pole = V(pos_w[0], pos_w[1], g) + Rz @ V(sx * 0.45 * self.s, 0.5, sh.z - 0.3 * self.s)
            self.hand_w(sd, f, W, d, n, pole)

def lin(o):
    ad = o.animation_data
    if not ad or not ad.action: return
    for fc in fcurves_of(ad.action):
        for k in fc.keyframe_points: k.interpolation = 'LINEAR'

def fcurves_of(act):
    try: return list(act.fcurves)
    except Exception:
        out = []
        for L in act.layers:
            for st in L.strips:
                for cb in st.channelbags: out += list(cb.fcurves)
        return out

def const_keys(o, path, f, val, idx=None):
    setattr(o, path, val) if idx is None else None
    o.keyframe_insert(path, frame=f)

# =========================================================================== characters
G = Char("Gunman", 1.22)
P = Char("President", 1.28)
AA = Char("ActorA", 1.16)
AB = Char("ActorB", 1.24)
SOL = [Char("Soldier%d" % i, 1.0) for i in (1, 2, 3)]
for c in [G, P, AA, AB] + SOL:
    for s in "LR": apply_pose(c.o, s, "relaxed", 1)
PARK = {"Gunman": V(300, 0, 0), "President": V(303, 0, 0), "ActorA": V(306, 0, 0), "ActorB": V(309, 0, 0),
        "Soldier1": V(312, 0, 0), "Soldier2": V(315, 0, 0), "Soldier3": V(318, 0, 0)}
def park(c, f):
    p = PARK[c.o.name]; c.stand(f, p, 0); c.hang(f, p, 0)

# --------------------------------------------------------------------------- props
CP = coll("Props")
pistol = glb_asset("pistol", CP, target_size=0.22, axis=1)
# barrel along +-Y: find the handle (lowest region) and the muzzle (far end of the barrel)
vs = [v.co for v in pistol.data.vertices]
zmin = min(v.z for v in vs); zmax = max(v.z for v in vs); ymin = min(v.y for v in vs); ymax = max(v.y for v in vs)
low = [v for v in vs if v.z < zmin + 0.25 * (zmax - zmin)]
hy = sum(v.y for v in low) / len(low)
muzzle_y = ymin if abs(ymin - hy) > abs(ymax - hy) else ymax
top = [v for v in vs if abs(v.y - muzzle_y) < 0.01]
muzzle = V(0, muzzle_y, sum(v.z for v in top) / max(1, len(top)))
handle = V(0, hy, zmin + 0.42 * (zmax - zmin))
# re-origin the pistol at the handle with the barrel pointing -Y (forward for a character facing -Y)
pistol.data.transform(Matrix.Translation(-handle))
if muzzle_y > hy: pistol.data.transform(Matrix.Rotation(math.pi, 4, 'Z')); muzzle = V(0, -(muzzle.y - hy), muzzle.z - handle.z)
else: muzzle = muzzle - handle
MUZ = muzzle.copy()
print("PISTOL handle", tuple(handle), "muzzle(local)", tuple(MUZ))
pistol.name = "Pistol"


# ---------------------------------------------------------------- emissive fire particles (Geometry Nodes, keyed clock T, no cache)
def fire_material():
    m = bpy.data.materials.get("FireBlob")
    if m: return m
    m = bpy.data.materials.new("FireBlob"); n, l = nodes_of(m); n.clear()
    out = n.new('ShaderNodeOutputMaterial'); at = n.new('ShaderNodeAttribute'); at.attribute_type = 'INSTANCER'; at.attribute_name = "heat"
    ramp = n.new('ShaderNodeValToRGB'); el = ramp.color_ramp.elements
    el[0].position = 0.0; el[0].color = (1.0, 0.72, 0.18, 1); el[1].position = 1.0; el[1].color = (0.55, 0.04, 0.01, 1)
    mid = el.new(0.3); mid.color = (1.0, 0.38, 0.04, 1)
    em = n.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 2.2
    tr = n.new('ShaderNodeBsdfTransparent'); mx = n.new('ShaderNodeMixShader')
    pw = n.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 2.0
    l.new(at.outputs['Fac'], ramp.inputs[0]); l.new(ramp.outputs[0], em.inputs['Color'])
    l.new(at.outputs['Fac'], pw.inputs[0]); l.new(pw.outputs[0], mx.inputs[0])
    l.new(em.outputs[0], mx.inputs[1]); l.new(tr.outputs[0], mx.inputs[2]); l.new(mx.outputs[0], out.inputs[0])
    try: m.blend_method = 'HASHED'
    except Exception: pass
    return m
FIRE_T = []
def fire_tree(name, Wd, Dp, H, N, rad, speed):
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nd = ng.nodes; lk = ng.links
    gout = nd.new('NodeGroupOutput'); nd.new('NodeGroupInput')
    T = nd.new('ShaderNodeValue'); T.name = "T"; FIRE_T.append(ng)
    pts = nd.new('GeometryNodePoints'); pts.inputs['Count'].default_value = N
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
def fire_emitter(name, loc, Wd, Dp, H, N, rad, speed, parent=None, coll_=None):
    me = bpy.data.meshes.new(name); o = bpy.data.objects.new(name, me); (coll_ or CP).objects.link(o)
    md = o.modifiers.new("Fire", 'NODES'); md.node_group = fire_tree(name + "_GN", Wd, Dp, H, N, rad, speed)
    o.location = loc; o.visible_shadow = False
    if parent: o.parent = parent
    return o

def torch_obj(name):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.022, radius2=0.03, depth=0.62)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 0.31))
    o = mesh_obj(name, bm, [pbr("TorchWood", "brown_planks_05", scale=2.0, tint=(0.8, 0.6, 0.4), bump=0.3)], CP); shade_smooth(o)
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.045, radius2=0.05, depth=0.14)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 0.66))
    w = mesh_obj(name + "_Wrap", bm, [flat("TorchWrap", (0.25, 0.16, 0.08), rough=0.9)], CP); w.parent = o; shade_smooth(w)
    fire_emitter(name + "_Fire", (0, 0, 0.70), 0.07, 0.07, 0.34, 45, 0.05, 0.9, parent=o)
    L = bpy.data.lights.new(name + "_Light", 'POINT'); L.energy = 60; L.color = (1.0, 0.55, 0.2); L.shadow_soft_size = 0.2
    lo = bpy.data.objects.new(name + "_Light", L); CP.objects.link(lo); lo.parent = o; lo.location = (0, 0, 0.85)
    return o
torches = [torch_obj("Torch%d" % i) for i in (1, 2, 3)]

def child_of_now(obj, rig, bone, f):
    """Child Of the bone with the inverse set at frame f (prop stays exactly where it is at f)"""
    sc.frame_set(int(f))
    mw = obj.matrix_world.copy()
    c = obj.constraints.new('CHILD_OF'); c.target = rig; c.subtarget = bone
    bpy.context.view_layer.update()
    PBm = rig.matrix_world @ rig.pose.bones[bone].matrix
    c.inverse_matrix = PBm.inverted()
    obj.matrix_world = mw
    obj.location = mw.translation; obj.rotation_euler = mw.to_euler(); obj.scale = mw.to_scale()
    bpy.context.view_layer.update()
    return c

# =========================================================================== THEATRE performance
CHP = Vector(sc["CHAIR_POS"]); CHY = sc["CHAIR_YAW"]
Rc = Matrix.Rotation(R_(CHY), 3, 'Z')
fwd_c = Rc @ V(0, -1, 0)                      # the president looks this way (toward the stage)
TH0, TH1 = ST["S01"], SE("S10")
F_FIRE = ST["S05"] + 40

# ---- president: seated in the armchair, watching; a laugh with the audience before the shot
def pres_seated(f, laugh=0.0, breath=0.0):
    c = P.use(); seat = CHP + Rc @ V(0, -0.15, 0.45)
    hip_w = seat + V(0, 0, 0.09 * c.s)
    pa = c.a(hip_w)
    c.H.key_root(f, pa, yaw=CHY, flex=-6 - 4 * laugh)
    c.H.key_spine(f, flex=8 + 6 * laugh + 1.5 * breath, head=(-4 + 10 * laugh, 4))
    for sd, sx in (("L", 1), ("R", -1)):
        foot = CHP + Rc @ V(sx * 0.17, -0.62, 0)
        c.H.key_foot(sd, f, c.a(foot).to_2d(), CHY)
        knee = CHP + Rc @ V(sx * 0.16, -0.48, 0.55)
        W = CHP + Rc @ V(sx * 0.17, -0.38, 0.50)
        c.hand_w(sd, f, W, Rc @ V(0, -1, -0.25), Rc @ V(0, 0, -1), CHP + Rc @ V(sx * 0.55, 0.1, 0.7))
PRES_END = SE("S06")
for f in range(TH0, PRES_END + 1, 6):
    u = (f - (F_FIRE - 28)) / 20.0
    laugh = math.sin(math.pi * min(1, max(0, u))) if 0 < u < 1 else 0.0
    pres_seated(f, laugh=laugh, breath=math.sin(f / 40.0))
pres_seated(PRES_END); park(P, PRES_END + 1); park(P, END_FRAME)

# ---- stage actors: a parlour comedy, big gestures; the laugh line peaks just before the shot
def actor(c, f, pos, yaw, arms_up=0.0, lean=0.0, head=(0, 0), stepw=0.0):
    c.stand(f, pos, yaw, flex=4 + lean, head=head, twist=8 * math.sin(f / 23.0))
    Rz = Matrix.Rotation(R_(yaw), 3, 'Z'); g = 0.0
    for sd, sx in (("L", 1), ("R", -1)):
        a = arms_up if sd == "L" else arms_up * 0.85
        sh = c.o.data.bones["upperarm01." + sd].head_local * c.s
        W = V(pos[0], pos[1], g) + Rz @ V(sx * (abs(sh.x) + 0.12 + 0.35 * a), -0.08 - 0.25 * a, sh.z - 0.55 * c.s + 0.55 * a)
        d = Rz @ V(sx * 0.6 * a, -0.2, -1 + 1.6 * a).normalized(); n = Rz @ V(-sx * (1 - a), -a, 0).normalized()
        c.hand_w(sd, f, W, d, n, V(pos[0], pos[1], g) + Rz @ V(sx * 0.6, 0.4, sh.z - 0.3))
        apply_pose(c.o, sd, "open_alarm" if a > 0.4 else "relaxed", f)
for f in range(TH0, TH1 + 1, 10):
    t = f / 60.0
    peak = max(0.0, 1 - abs(f - (F_FIRE - 15)) / 45.0)
    actor(AA, f, (4.75, 0.05), yaw_to(V(1, -0.9, 0)), arms_up=0.25 + 0.25 * math.sin(t * 2.1) ** 2 + 0.5 * peak, head=(-5, 10 * math.sin(t)))
    actor(AB, f, (3.55, -0.55), yaw_to(V(0.6, -1, 0)), arms_up=0.15 + 0.2 * abs(math.sin(t * 1.7)) + 0.4 * peak, lean=-10 * peak,
          head=(-12 * peak, -8))
for c in (AA, AB): park(c, TH1 + 1); park(c, END_FRAME)

# ---- gunman in the box: gun rises, aims at the back of the head, fires, lowers, turns to the ledge
GPOS = CHP + Rc @ V(0.25, 1.70, 0) ; GPOS.z = BZ
G_YAW = yaw_to(fwd_c)
sc.frame_set(ST["S01"])
for f in list(range(TH0, ST["S06"], 6)) + [ST["S06"] + 32]:
    G.stand(f, (GPOS.x, GPOS.y), G_YAW, crouch=-0.015, flex=4, head=(4 if f > ST["S01"] + 80 else 0, 0), twist=-6)
    if f >= ST["S04"] and f < ST["S05"] + 30:
        G.H.key_spine(f, flex=9, twist=-8, head=(6, 0))
# left arm hangs relaxed all through the box
for f in range(TH0, ST["S06"] + 31, 12):
    Rz = Matrix.Rotation(R_(G_YAW), 3, 'Z')
    sh = G.o.data.bones["upperarm01.L"].head_local * G.s
    W = V(GPOS.x, GPOS.y, BZ) + Rz @ V(abs(sh.x) + 0.1, -0.06, sh.z - 0.58 * G.s)
    G.hand_w("L", f, W, Rz @ V(0, -0.15, -1).normalized(), Rz @ V(-1, 0, 0), V(GPOS.x, GPOS.y, BZ) + Rz @ V(0.55, 0.5, sh.z - 0.3))
Rz = Matrix.Rotation(R_(G_YAW), 3, 'Z')
sc.frame_set(ST["S01"])
head_P = P.world_bone("head", F_FIRE - 40).translation + V(0, 0, 0.06)
shR = G.world_bone("upperarm01.R", ST["S01"] + 120).translation
aim_dir = (head_P - shR).normalized()
# gun world transforms: low at the thigh (pointing down-forward) -> raised, muzzle ~0.6 m behind the head
def gun_matrix(pos, fwd, up_hint=V(0, 0, 1)):
    y = -fwd.normalized(); x = up_hint.cross(y).normalized(); z = y.cross(x)
    # pistol local: barrel -Y, up +Z
    return Matrix.Translation(pos) @ Matrix((x, y, z)).transposed().to_4x4()
low_pos = V(GPOS.x, GPOS.y, BZ) + Rz @ V(-0.30, -0.12, 0.80)
low_fwd = Rz @ V(0, -1, -1.3)
aim_pos = shR + aim_dir * 0.47 + V(0, 0, -0.03)
G_AIM = gun_matrix(aim_pos, aim_dir)
G_LOW = gun_matrix(low_pos, low_fwd)
# grip once at the aim pose; afterwards the hand is driven from the gun's transform (gun stays in the fingers)
FG = ST["S01"] + 120
pistol.matrix_world = G_AIM
bpy.context.view_layer.update()
_pb = G.o.pose.bones["Pole_elbow.R"]
_pb.location = G.R.rest("Pole_elbow.R").to_3x3().inverted() @ (G.a(V(GPOS.x, GPOS.y, BZ) + Rz @ V(-0.75, 0.1, 0.9)) - G.R.BN["Pole_elbow.R"].head_local)
_pb.keyframe_insert("location", frame=FG, group="Pole_elbow.R")
apply_pose(G.o, "R", "relaxed", FG)
rep = grip_object(G.o, "R", FG, pistol, pistol.matrix_world @ V(0.0, 0.0, -0.005), (pistol.matrix_world.to_3x3() @ V(-1, 0, 0)).normalized(),
                  finger_dir=(pistol.matrix_world.to_3x3() @ V(0, -0.3, -1)).normalized(), finger_radius=0.021)
print("GRIP", rep)
def curl_free(rig, sd, rep, f):
    pr = _pose_rots(rig, sd, "power_fist")
    for k in (3, 4, 5):
        if rep.get("finger%d-3.%s" % (k, sd)) is None:
            for j in (1, 2, 3):
                n = "finger%d-%d.%s" % (k, j, sd); pb = rig.pose.bones[n]
                pb.rotation_quaternion = pr[n]; pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
curl_free(G.o, "R", rep, FG)
sc.frame_set(FG)
pbH = G.o.pose.bones["IK_hand.R"]; H0 = pbH.matrix.copy()            # armature space
fing = {pb.name: pb.rotation_quaternion.copy() for pb in G.o.pose.bones if pb.name.startswith("finger") and pb.name.endswith(".R")}
def key_gun(f, Mgun):
    A = G.o.matrix_world.inverted() @ Mgun @ G_AIM.inverted() @ G.o.matrix_world @ H0
    G.R.key_world("IK_hand.R", f, A)
    pb = G.o.pose.bones["Pole_elbow.R"]; n = "Pole_elbow.R"
    pole = G.a(V(GPOS.x, GPOS.y, BZ) + Rz @ V(-0.75, 0.1, 0.9))
    pb.location = G.R.rest(n).to_3x3().inverted() @ (pole - G.R.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)
def blend_gun(u):
    u = smooth(u)
    loc = G_LOW.translation.lerp(G_AIM.translation, u)
    q = G_LOW.to_quaternion().slerp(G_AIM.to_quaternion(), u)
    return Matrix.Translation(loc) @ q.to_matrix().to_4x4()
RAISE0, RAISE1 = ST["S01"] + 20, ST["S01"] + 110
for f in list(range(TH0, RAISE0, 10)) + list(range(RAISE0, RAISE1 + 1, 3)):
    key_gun(f, blend_gun((f - RAISE0) / (RAISE1 - RAISE0)) if f >= RAISE0 else G_LOW)
for f in range(RAISE1 + 6, F_FIRE + 1, 6):            # steady aim, a tiny breath tremor
    key_gun(f, Matrix.Translation(V(0, 0, 0.004 * math.sin(f / 9.0))) @ G_AIM)
for f in range(F_FIRE + 1, F_FIRE + 21, 2):            # recoil kick (follows the hand, no finger change)
    u = (f - F_FIRE) / 20.0; kick = math.sin(math.pi * min(1, u * 1.6)) * (1 - u)
    key_gun(f, G_AIM @ Matrix.Translation(V(0, 0.04 * kick, 0)) @ Matrix.Rotation(R_(14 * kick), 4, 'X'))
LOW0, LOW1 = ST["S06"] + 6, ST["S06"] + 40
for f in range(F_FIRE + 22, LOW0, 6): key_gun(f, G_AIM)
for f in range(LOW0, LOW1 + 1, 3): key_gun(f, blend_gun(1 - (f - LOW0) / (LOW1 - LOW0)))
for n, q in fing.items():
    pb = G.o.pose.bones[n]
    for f in (TH0, ST["S06"] + 55):
        pb.rotation_quaternion = q; pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
pistol.matrix_world = G_AIM
child_of_now(pistol, G.o, "wrist.R", FG)
key_vis(pistol, 1, False); key_vis(pistol, TH0, True); key_vis(pistol, ST["S07"], False)
# S06: lowers the gun, glances back over his shoulder at the door, then snaps his head to the ledge
for off, hd, fl in ((0, (6, 0), 9), (14, (-4, 30), 6), (26, (-2, 34), 6), (34, (0, -25), 10)):
    G.H.key_spine(ST["S06"] + off, flex=fl, twist=-6, head=hd)
# turn and two steps to the ledge (S06 end)
STEP0 = ST["S06"] + 35
ledge_stand = GPOS + (V(BX0 + 0.55, GPOS.y + 0.2, BZ) - GPOS).normalized() * 0.45
path_box = lambda f: GPOS.to_2d().lerp(ledge_stand.to_2d(), smooth((f - STEP0) / (SE("S06") + 1 - STEP0)))
yaw_box = pchip([(STEP0, G_YAW), (STEP0 + 30, yaw_to(V(-1, 0.1, 0))), (SE("S06") + 1, yaw_to(V(-1, 0.1, 0)))])
G.use(); G.H.walk(lambda f: G.a((*path_box(f), 0)), yaw_box, STEP0, SE("S06"), stride=0.62 / G.s, lift=0.08 / G.s)
for f in range(STEP0, SE("S06") + 1, 6):
    G.hang(f, (*path_box(f), BZ), yaw_box(f), swing=(0.06 * math.sin(f / 7.0), -0.06 * math.sin(f / 7.0)))
apply_pose(G.o, "R", "relaxed", ST["S06"] + 70)

# ---- S07/S08: on the ledge, crouch, spring, fall 4.6 m to the stage, land, knee buckles
LEDGE = V(BX0 - 0.06, -1.6, BZ + 0.83)
JYAW = yaw_to(V(-1, -0.05, 0))
LAUNCH = ST["S07"] + 100; LAND = LAUNCH + 50
LAND_P = V(BX0 - 1.45, -1.75, 0.0)
hipz = G.H.root_head.z * G.s
def g_air(f):
    t = (f - LAUNCH) / 60.0; T = (LAND - LAUNCH) / 60.0
    x = LEDGE.lerp(LAND_P, t / T)
    z0 = LEDGE.z + hipz - 0.18; z1 = hipz - 0.05
    vz = (z1 - z0 + 4.905 * T * T) / T
    return V(x.x, x.y, z0 + vz * t - 4.905 * t * t)
Rj = Matrix.Rotation(R_(JYAW), 3, 'Z')
def feet_at(f, base, spread=0.13, fwd=(0.0, 0.0), lift=(0.0, 0.0), pitch=(0, 0)):
    for i, sd in enumerate("LR"):
        sx = 1 if sd == "L" else -1
        p = base + Rj @ V(sx * spread, -fwd[i], 0)
        G.use(); z = (base.z + lift[i])
        a = G.a(V(p.x, p.y, 0)); G.H.key_foot(sd, f, a.to_2d(), JYAW, lift=z / G.s, pitch=pitch[i])
for f in range(ST["S07"], LAUNCH + 1, 4):
    u = smooth((f - (ST["S07"] + 30)) / 50.0)
    root = V(LEDGE.x, LEDGE.y, LEDGE.z + hipz - 0.03 - 0.30 * u)
    G.H.key_root(f, G.a(root), yaw=JYAW, flex=6 + 22 * u)
    G.H.key_spine(f, flex=8 + 20 * u, head=(-14 * u, 0))
    feet_at(f, V(LEDGE.x - 0.05, LEDGE.y, 0) + V(0, 0, LEDGE.z), spread=0.11, fwd=(0.04, -0.04))
    for sd, sx in (("L", 1), ("R", -1)):
        W = root + Rj @ V(sx * 0.32, 0.25 * u - 0.05, -0.38 + 0.05 * u)
        G.hand_w(sd, f, W, Rj @ V(0, 0.3 * u, -1).normalized(), Rj @ V(-sx, 0, 0), root + Rj @ V(sx * 0.5, 0.5, -0.1))
for f in range(LAUNCH, LAND + 1, 2):
    t = (f - LAUNCH) / (LAND - LAUNCH)
    root = g_air(f); tuck = math.sin(math.pi * t)
    G.H.key_root(f, G.a(root), yaw=JYAW, flex=20 * (1 - t) + 8)
    G.H.key_spine(f, flex=10, head=(-8 + 14 * t, 0))
    base = root - V(0, 0, hipz - 0.10 + 0.25 * tuck)
    feet_at(f, base, spread=0.14, fwd=(0.10 * tuck, -0.05 * tuck), lift=(0, 0), pitch=(10 * tuck, -5 * tuck))
    for sd, sx in (("L", 1), ("R", -1)):
        W = root + Rj @ V(sx * (0.42 + 0.1 * tuck), -0.05, 0.05 + 0.25 * tuck)
        G.hand_w(sd, f, W, Rj @ V(sx * 0.5, -0.3, 0.6).normalized(), Rj @ V(0, 1, 0), root + Rj @ V(sx * 0.6, 0.4, 0.2))
        apply_pose(G.o, sd, "open_alarm", f) if f == LAUNCH else None
# landing: absorb, left knee buckles to the boards, left palm flat on the floor
KNEEL0, KNEEL1 = LAND + 14, LAND + 52
for f in range(LAND, SE("S09") + 1, 2):
    a = smooth((f - LAND) / 14.0); k = smooth((f - KNEEL0) / (KNEEL1 - KNEEL0))
    root = V(LAND_P.x, LAND_P.y, hipz - 0.05 - 0.30 * a - 0.12 * k) + Rj @ V(0, 0.08 * k, 0)
    if f > SE("S09") - 40: root.z += 0.01 * math.sin(f / 6.0)
    G.H.key_root(f, G.a(root), yaw=JYAW, flex=12 + 20 * a - 10 * k, side=-6 * k)
    G.H.key_spine(f, flex=14 + 10 * a, head=(-10 + 18 * k, -10 * k))
    # right foot planted forward, left foot slides back and the shin lies on the floor
    pR = LAND_P + Rj @ V(-0.14, -0.10, 0); G.use(); G.H.key_foot("R", f, G.a(pR).to_2d(), JYAW)
    pL = LAND_P + Rj @ V(0.14, 0.05 + 0.55 * k, 0)
    G.H.key_foot("L", f, G.a(pL).to_2d(), JYAW, lift=0.0, pitch=-55 * k)
    # hands: right hand on the right knee, left palm down on the boards beside the left knee
    WR = root + Rj @ V(-0.12, -0.32, -0.12 - 0.05 * k)
    G.hand_w("R", f, WR, Rj @ V(0, -1, -0.4).normalized(), V(0, 0, -1), root + Rj @ V(-0.6, 0.3, 0))
    WL = (1 - k) * (root + Rj @ V(0.36, -0.1, -0.3)) + k * (LAND_P + Rj @ V(0.42, -0.05, 0.06))
    G.hand_w("L", f, WL, Rj @ V(0.1, -1, -0.15 * k).normalized(), (1 - k) * (Rj @ V(-1, 0, 0)) + k * V(0, 0, -1), root + Rj @ V(0.7, 0.3, 0))
    if f == LAND: apply_pose(G.o, "L", "relaxed", f); apply_pose(G.o, "R", "relaxed", f)
    if f == KNEEL1: apply_pose(G.o, "L", "flat_palm", f, amount=0.8)
# ---- S10: rises and limps toward camera (stage left), left hand on the left thigh
RISE0, RISE1 = ST["S10"], ST["S10"] + 45
LIMP0 = RISE1
limp_end = LAND_P + Rj @ V(0, -2.6, 0)
for f in range(RISE0, RISE1 + 1, 3):
    u = smooth((f - RISE0) / (RISE1 - RISE0))
    root = V(LAND_P.x, LAND_P.y, hipz - 0.47 + 0.42 * u) + Rj @ V(0, 0.08 * (1 - u), 0)
    G.H.key_root(f, G.a(root), yaw=JYAW, flex=22 - 16 * u, side=-6 * (1 - u))
    G.H.key_spine(f, flex=24 - 14 * u, head=(8 - 6 * u, -10))
    pR = LAND_P + Rj @ V(-0.14, -0.10, 0); G.use(); G.H.key_foot("R", f, G.a(pR).to_2d(), JYAW)
    pL = LAND_P + Rj @ V(0.14, 0.60 - 0.55 * u, 0)
    G.H.key_foot("L", f, G.a(pL).to_2d(), JYAW, lift=0.0, pitch=-55 * (1 - u))
    G.hand_w("R", f, root + Rj @ V(-0.30, -0.08, -0.40), Rj @ V(0, -0.1, -1).normalized(), Rj @ V(1, 0, 0), root + Rj @ V(-0.6, 0.4, 0))
    WL = (1 - u) * (LAND_P + Rj @ V(0.42, -0.05, 0.06)) + u * (root + Rj @ V(0.15, -0.20, -0.28))
    G.hand_w("L", f, WL, Rj @ V(0.0, -0.4, -1).normalized(), (1 - u) * V(0, 0, -1) + u * (Rj @ V(0, 1, 0.3)), root + Rj @ V(0.7, 0.3, 0))
apply_pose(G.o, "L", "cup_hold", RISE1)
limp_path = lambda f: G.a((LAND_P + (limp_end - LAND_P) * smooth((f - LIMP0) / (SE("S10") + 40 - LIMP0))).to_3d()).to_2d().to_3d()
G.use(); G.H.walk(lambda f: G.a((LAND_P.lerp(limp_end, min(1, (f - LIMP0) / (SE("S10") + 40 - LIMP0))))), lambda f: JYAW,
                  LIMP0, SE("S10"), stride=0.5 / G.s, duty=0.68, lift=0.05 / G.s, bob=0.045 / G.s, lean=10)
sc.frame_set(LIMP0)
for f in range(LIMP0, SE("S10") + 1, 2):       # left hand rides on the left thigh above the knee
    M = G.world_bone("upperleg02.L", f)
    W = M @ V(0.0, M.to_3x3().col[1].length * 0.0 + 0.05, 0) if False else (M.translation + (M.to_3x3() @ V(0, 1, 0)).normalized() * 0.20 + (G.o.matrix_world.to_3x3() @ Rj @ V(0, -1, 0)).normalized() * 0.0)
    thigh_dir = (M.to_3x3() @ V(0, 1, 0)).normalized(); fwd = Rj @ V(0, -1, 0)
    W = M.translation + thigh_dir * 0.14 * G.s + fwd * 0.13 + Rj @ V(0.04, 0, 0) + V(0, 0, 0.03)
    G.hand_w("L", f, W, (thigh_dir + fwd * 0.3).normalized(), -fwd, M.translation + Rj @ V(0.6, 0.4, 0.1))
    G.hand_w("R", f, G.world_bone("upperarm01.R").translation + Rj @ V(-0.08, -0.04 * math.sin(f / 8.0), -0.55),
             Rj @ V(0, -0.15, -1).normalized(), Rj @ V(1, 0, 0), M.translation + Rj @ V(-0.9, 0.4, 0.3))
# crack flash on the left shin (S09): stylised, clean, no wound
bm = bmesh.new(); pts = []
for i in range(14):
    a = i * math.pi / 7; r = 0.055 if i % 2 == 0 else 0.022
    pts.append(bm.verts.new((r * math.cos(a), 0, r * math.sin(a))))
bm.faces.new(pts)
crack = mesh_obj("CrackFlash", bm, [flat("CrackRed", (1, 0.1, 0.05), emit=(1, 0.12, 0.05), emit_str=8.0)], CP)
crack.visible_shadow = False
FC = ST["S09"] + 15
sc.frame_set(FC)
_ll = G.o.pose.bones["lowerleg01.L"]; _mid = G.o.matrix_world @ ((_ll.head + _ll.tail) / 2)
crack.location = _mid + V(0, 0.075, 0.02); crack.rotation_euler = (0, 0, math.pi)
for f, s_ in ((1, 0.0), (FC - 1, 0.0), (FC + 3, 2.6), (FC + 10, 2.1), (FC + 40, 1.9), (FC + 60, 0.0)):
    crack.scale = (s_,) * 3; crack.keyframe_insert("scale", frame=f)
key_vis(crack, 1, False); key_vis(crack, FC - 1, True); key_vis(crack, FC + 61, False)

# =========================================================================== STREET: escape on horseback
HR = Rig(bpy.data.objects["Horse"]); horse = HR.o; horse.location = (0, 0, 0)
for pb in horse.pose.bones: pb.rotation_mode = 'QUATERNION'
def ground_z(x, y):  # horse rig is unscaled; anim_lib's quad helpers call ground_z with world xy
    s = CUR_S[0]; return ground_w(x * s, y * s) / s
def quad_gallop(rig, path, f0, f1, stride=3.0, lift=0.32, bob=0.07):
    """transverse gallop: HL .0, HR .1, FL .5, FR .6; duty .35; hooves planted, no slide"""
    BN = rig.BN; tr = rig.rest("torso")
    off = {k: BN["IK_hoof." + k].head_local - tr.translation for k in LEGS}
    phase = {"HL": 0.0, "HR": 0.1, "FL": 0.5, "FR": 0.6}; duty = 0.35
    frames = list(range(f0, f1 + 1)); dist = [0.0]
    for a, b in zip(frames, frames[1:]): dist.append(dist[-1] + (path(b) - path(a)).to_2d().length)
    def heading(f):
        a, b = path(max(f0, f - 2)), path(min(f1, f + 2)); d = (b - a).to_2d()
        return math.atan2(d.x, -d.y)
    def foot_world(k, f):
        p = path(f); o = Matrix.Rotation(heading(f), 3, 'Z') @ off[k]
        return Vector((p.x + o.x, p.y + o.y, BN["IK_hoof." + k].head_local.z))
    for k in LEGS:
        n = "IK_hoof." + k; cyc = [d / stride + phase[k] for d in dist]; per = {}
        for i, c in enumerate(cyc): per.setdefault(int(math.floor(c)), []).append(i)
        plant = {}
        for pid, idxs in per.items():
            st = [i for i in idxs if (cyc[i] % 1.0) < duty]
            if st:
                im = min(st, key=lambda i: abs((cyc[i] % 1.0) - duty / 2)); plant[pid] = (foot_world(k, frames[im]), heading(frames[im]))
        first = (foot_world(k, frames[0]), heading(frames[0])); last = (foot_world(k, frames[-1]), heading(frames[-1]))
        for i, f in enumerate(frames):
            pid = int(math.floor(cyc[i])); fr = cyc[i] % 1.0
            if fr < duty:
                pos, h = plant.get(pid, first if i < len(frames) / 2 else last); z = 0.0; tu = 0.0
            else:
                a = plant.get(pid, first); b = plant.get(pid + 1, last); s_ = (fr - duty) / (1 - duty)
                pos = a[0].lerp(b[0], smooth(s_)); h = a[1] + (b[1] - a[1]) * smooth(s_); z = lift * math.sin(math.pi * s_); tu = 0.5 * math.sin(math.pi * s_)
            rig.key_world(n, f, hoof_matrix(rig, n, pos.to_2d(), h, lift=z, toe_up=tu))
    for i, f in enumerate(frames):
        p = path(f); h = heading(f); cyc = (dist[i] / stride) % 1.0
        z = tr.translation.z + bob * math.cos(2 * math.pi * (cyc - 0.15)); pitch = R_(4) * math.sin(2 * math.pi * cyc)
        M = Matrix.Translation(Vector((p.x, p.y, z))) @ Matrix.Rotation(h, 4, 'Z') @ Matrix.Rotation(pitch, 4, 'X') @ \
            Matrix.Translation(-tr.translation) @ tr
        rig.key_world("torso", f, M)
        if "head" in rig.PB: rig.key_rot("head", f, [("X", 8 * math.sin(2 * math.pi * cyc))])
        if "neck1" in rig.PB: rig.key_rot("neck1", f, [("X", -6 * math.sin(2 * math.pi * cyc + 0.6))])
CUR_S[0] = 1.0
H_S11 = (ST["S11"], SE("S11")); H_S12 = (ST["S12"], SE("S12"))
p11 = lambda f: V(99.2, 20.0 - 10.5 * (f - H_S11[0]) / 60.0, 0)
p12 = lambda f: V(102.0, 18.0 - 8.0 * (f - H_S12[0]) / 60.0, 0)
quad_gallop(HR, p11, H_S11[0], H_S11[1], stride=3.4)
quad_gallop(HR, p12, H_S12[0], H_S12[1], stride=3.0)
for f in (1, H_S11[0] - 1): quad_hold(HR, f, V(150, 30, 0), 0.0)
for f in (H_S12[1] + 1, END_FRAME): quad_hold(HR, f, V(150, 30, 0), 0.0)
# rider: pelvis on the saddle seat, legs outside the barrel, feet at the stirrups, hands at the reins over the withers
SEAT = V(0, 0.22, 1.68)                         # horse rest space (saddle seat)
def rider(f, lean=12.0):
    sc.frame_set(f)
    Mt = horse.matrix_world @ horse.pose.bones["torso"].matrix @ HR.rest("torso").inverted()   # rest -> posed
    hd = math.degrees(math.atan2(*(lambda d: (d.x, -d.y))(Mt.to_3x3() @ V(0, -1, 0))))
    seat = Mt @ SEAT
    root = seat + Mt.to_3x3() @ V(0, 0.02, 0.10)
    G.use(); G.H.key_root(f, G.a(root), yaw=hd, flex=-lean * 0.4, side=0)
    G.H.key_spine(f, flex=lean, head=(-lean * 0.8, 0))
    for sd, sx in (("L", 1), ("R", -1)):
        st = Mt @ V(sx * 0.56, 0.02, 1.02)
        a = G.a(st); G.H.key_foot(sd, f, a.to_2d(), hd, lift=(st.z - G.H.ankle[sd].z * G.s) / G.s, pitch=0)
        pb = G.o.pose.bones["Pole_knee." + sd]; n = "Pole_knee." + sd
        pole = G.a(Mt @ V(sx * 1.2, -0.8, 1.35)); pb.location = G.R.rest(n).to_3x3().inverted() @ (pole - G.R.BN[n].head_local)
        pb.keyframe_insert("location", frame=f, group=n)
        W = Mt @ V(sx * 0.11, -0.38, 1.74)
        G.hand_w(sd, f, W, Mt.to_3x3() @ V(-sx * 0.3, -1, -0.3), Mt.to_3x3() @ V(-sx, 0, -0.4), Mt @ V(sx * 0.55, 0.1, 1.6))
for rng in (H_S11, H_S12):
    for f in list(range(rng[0], rng[1] + 1, 2)) + [rng[1]]: rider(f, lean=14 if rng is H_S12 else 10)
    apply_pose(G.o, "L", "wrap_grip", rng[0], amount=0.7); apply_pose(G.o, "R", "wrap_grip", rng[0], amount=0.7)

# =========================================================================== STREET: manhunt (soldiers jog with torches)
M0, M1 = ST["S13"], SE("S13")
for c in SOL:
    park(c, 1); park(c, M0 - 1)
def key_pole(c, s, f, W):
    n = "Pole_elbow." + s; pb = c.o.pose.bones[n]
    pb.location = c.R.rest(n).to_3x3().inverted() @ (c.a(W) - c.R.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)
for i, (c, x0, delay) in enumerate(zip(SOL, (98.6, 100.8, 102.6), (0, 8, 14))):
    y0 = 12.0 + 1.1 * i
    path = lambda f, x0=x0, y0=y0, d=delay: V(x0, y0 - 2.4 * max(0, f - M0 - d) / 60.0, 0)
    c.use(); c.H.walk(lambda f, path=path, c=c: c.a(path(f)), lambda f: 0.0, M0, M1, stride=1.25 / c.s, duty=0.45, lift=0.13, bob=0.035, lean=10)
    t = torches[i]
    # torch hand: right forearm forward at chest height (moves with the root), left arm swings bent
    FT = M0
    sc.frame_set(FT)
    def rhand(f, c=c, path=path):
        sc.frame_set(f); ch = c.world_bone("spine01")
        p = path(f); base = V(p.x, p.y, ch.translation.z)
        return base + V(-0.20, -0.36, -0.10)
    Wt = rhand(FT)
    for f in list(range(M0, M1 + 1, 2)) + [M1]:
        p = path(f); key_pole(c, "R", f, V(p.x - 0.7, p.y + 0.3, 0.9))
    t.matrix_world = Matrix.Translation(Wt) @ Matrix.Rotation(R_(16), 4, 'X') @ Matrix.Translation(V(0, 0, -0.22))
    bpy.context.view_layer.update()
    Cax = t.matrix_world @ V(0, 0, 0.22)
    rep = grip_object(c.o, "R", FT, t, Cax + V(-0.026, 0, 0), V(1, 0, 0), finger_dir=V(0, -1, 0), finger_radius=0.017)
    print("TORCH GRIP", c.o.name, rep)
    curl_free(c.o, "R", rep, FT)
    sc.frame_set(FT); H0t = c.o.pose.bones["IK_hand.R"].matrix.copy(); T0 = t.matrix_world.copy()
    fr = {pb.name: pb.rotation_quaternion.copy() for pb in c.o.pose.bones if pb.name.startswith("finger") and pb.name.endswith(".R")}
    for n, q in fr.items():
        pb = c.o.pose.bones[n]
        for ff in (M0, M1): pb.rotation_quaternion = q; pb.keyframe_insert("rotation_quaternion", frame=ff, group=n)
    for f in list(range(M0, M1 + 1, 2)) + [M1]:
        Wf = rhand(f); D = Matrix.Translation(Wf - Wt)
        c.R.key_world("IK_hand.R", f, c.o.matrix_world.inverted() @ D @ c.o.matrix_world @ H0t)
        p = path(f); cyc = math.sin((p.y - y0) / 1.25 * math.pi)
        sh = c.o.data.bones["upperarm01.L"].head_local
        WL = V(p.x, p.y, 0) + V(sh.x + 0.12, -0.05 - 0.22 * cyc, sh.z - 0.42)
        c.hand_w("L", f, WL, V(0, -0.6 - 0.4 * cyc, -0.6).normalized(), V(-1, 0, 0), V(p.x, p.y, 0) + V(0.5, 0.6, sh.z - 0.3))
    child_of_now(t, c.o, "wrist.R", FT)
    apply_pose(c.o, "L", "relaxed", M0)

# =========================================================================== BARN
BA0, BA1 = ST["S14"], SE("S15")
X1 = 200.0
GB = V(X1 + 1.25, 2.5, 0)                 # behind the bales (door is at -y)
BYAW = yaw_to(V(-0.15, -1, 0))
RISE_B0, RISE_B1 = ST["S14"] + 60, ST["S14"] + 120
HANDS0, HANDS1 = ST["S15"] + 30, ST["S15"] + 75
RzB = Matrix.Rotation(R_(BYAW), 3, 'Z')
for f in range(BA0, BA1 + 1, 3):
    u = smooth((f - RISE_B0) / (RISE_B1 - RISE_B0))
    crouch = 0.55 * (1 - u)
    root = GB + V(0, 0, hipz - 0.03 - crouch) + RzB @ V(0, 0.10 * (1 - u), 0)
    G.H.key_root(f, G.a(root), yaw=BYAW, flex=6 + 18 * (1 - u))
    hv = smooth((f - HANDS0) / (HANDS1 - HANDS0))
    G.H.key_spine(f, flex=8 + 18 * (1 - u) - 4 * hv, head=(6 * (1 - u) - 18 * hv, 10 * math.sin(f / 35.0) * (1 - hv)))
    for sd, sx in (("L", 1), ("R", -1)):
        G.use(); xy = GB + RzB @ V(sx * 0.15, 0.06 * sx, 0); G.H.key_foot(sd, f, G.a(xy).to_2d(), BYAW)
        pb = G.o.pose.bones["Pole_knee." + sd]; n = "Pole_knee." + sd
        pole = G.a(GB + RzB @ V(sx * 0.2, -0.8, 0.5)); pb.location = G.R.rest(n).to_3x3().inverted() @ (pole - G.R.BN[n].head_local)
        pb.keyframe_insert("location", frame=f, group=n)
        sh = G.o.data.bones["upperarm01." + sd].head_local * G.s
        Wdown = root + RzB @ V(sx * 0.30, -0.12 - 0.15 * (1 - u), -0.30 + 0.12 * (1 - u))
        Wup = GB + RzB @ V(sx * 0.38, -0.18, sh.z + 0.02)
        W = Wdown.lerp(Wup, hv)
        d = (RzB @ V(0, -0.3, -1)).normalized().lerp((RzB @ V(sx * 0.1, 0, 1)).normalized(), hv)
        nrm = (RzB @ V(-sx, 0, 0)).lerp(RzB @ V(0, -1, 0), hv)
        G.hand_w(sd, f, W, d, nrm, GB + RzB @ V(sx * 0.7, 0.3, sh.z - 0.4 + 0.1 * hv))
apply_pose(G.o, "L", "relaxed", BA0); apply_pose(G.o, "R", "relaxed", BA0)
apply_pose(G.o, "L", "relaxed", HANDS0); apply_pose(G.o, "R", "relaxed", HANDS0)
apply_pose(G.o, "L", "open_alarm", HANDS1); apply_pose(G.o, "R", "open_alarm", HANDS1)
# soldiers at the door with torches, stepping in (they keep their torches from S13)
for i, (c, x) in enumerate(zip(SOL, (X1 - 1.5, X1 - 0.35, X1 + 2.5))):
    p0 = V(x, -7.4 - 0.3 * (i == 1), 0); p1 = V(x * 0.85 + X1 * 0.15, -5.6 + 0.4 * (i == 1), 0)
    W0 = ST["S14"] + 20 + 10 * i; W1 = W0 + 90
    pth = lambda f, p0=p0, p1=p1, W0=W0, W1=W1: p0.lerp(p1, min(1, max(0, (f - W0) / (W1 - W0))))
    yaw = yaw_to(V(X1 + 1.25, 2.3, 0) - p1)
    c.use(); c.stand(BA0, p0, yaw)
    c.H.walk(lambda f, pth=pth, c=c: c.a(pth(f)), lambda f, yaw=yaw: yaw, W0, W1, stride=0.7 / c.s, lift=0.08)
    for f in (W1 + 2, BA1): c.stand(f, p1, yaw)
    # simple: reuse the S13 relative hand matrix (hand in front of the chest), keyed per frame
    sc.frame_set(M0); Hs = c.o.pose.bones["IK_hand.R"].matrix.copy()
    sc.frame_set(M0); ch0 = c.world_bone("spine01").translation; p_ = c.o.matrix_world.inverted() @ ch0
    for f in range(BA0, BA1 + 1, 3):
        sc.frame_set(f); ch = c.world_bone("spine01").translation
        yw = yaw
        Mrel = Matrix.Translation(c.a(ch)) @ Matrix.Rotation(R_(yw), 4, 'Z') @ Matrix.Translation(-p_)
        c.R.key_world("IK_hand.R", f, Mrel @ Hs)
        key_pole(c, "R", f, V(pth(f).x, pth(f).y, 0) + Matrix.Rotation(R_(yw), 3, 'Z') @ V(-0.7, 0.3, 0.9))
        sh = c.o.data.bones["upperarm01.L"].head_local; Ry = Matrix.Rotation(R_(yw), 3, 'Z'); p = pth(f)
        c.hand_w("L", f, V(p.x, p.y, 0) + Ry @ V(sh.x + 0.12, -0.08, sh.z - 0.55), Ry @ V(0, -0.15, -1).normalized(), Ry @ V(-1, 0, 0),
                 V(p.x, p.y, 0) + Ry @ V(0.5, 0.6, sh.z - 0.3))
park(G, M0); park(G, SE("S13"))
for t in torches:
    key_vis(t, 1, False); key_vis(t, M0, True)
    for ch in t.children: key_vis(ch, 1, False); key_vis(ch, M0, True)

# barn fire: emissive particle emitters replace the flat cards; one keyed clock per tree (linear, no Scene Time)
for o in [o for o in bpy.data.objects if o.name.startswith(("FlameBack", "FlameL", "FlameRoof"))]:
    bpy.data.objects.remove(o, do_unlink=True)
BF = bpy.data.collections["BarnFire"]
fire_emitter("BarnFireBack", V(X1, 6.55, 0.0), 8.2, 0.5, 2.7, 700, 0.15, 1.4, coll_=BF)
fire_emitter("BarnFireLeft", V(X1 - 4.05, 2.0, 0.0), 0.5, 8.5, 2.1, 560, 0.14, 1.3, coll_=BF)
fire_emitter("BarnFireRoof", V(X1 - 2.3, 2.5, 3.35), 0.6, 8.0, 1.0, 220, 0.11, 1.0, coll_=BF)
for ng in FIRE_T:
    T = ng.nodes["T"]
    for f in (1, END_FRAME):
        T.outputs[0].default_value = f / 60.0; T.outputs[0].keyframe_insert("default_value", frame=f)
    for fc in fcurves_of(ng.animation_data.action):
        for k in fc.keyframe_points: k.interpolation = 'LINEAR'
for L in [o for o in bpy.data.objects if o.name.startswith("FireLight")]:
    e0 = L.data.energy
    for f in range(1, END_FRAME + 1, 6):
        L.data.energy = e0 * (0.8 + 0.35 * random.Random(f * 7 + len(L.name)).random()); L.data.keyframe_insert("energy", frame=f)
# muzzle flash + smoke puff (S05), keyed scale
bm = bmesh.new(); pts = []
for i in range(16):
    a = i * math.pi / 8; r = 0.09 if i % 2 == 0 else 0.035
    pts.append(bm.verts.new((r * math.cos(a), 0, r * math.sin(a))))
bm.faces.new(pts)
flash = mesh_obj("MuzzleFlash", bm, [flat("FlashMat", (1, 0.9, 0.5), emit=(1, 0.85, 0.4), emit_str=25.0)], CP); flash.visible_shadow = False
smoke_m = bpy.data.materials.new("SmokeVol"); _n, _l = nodes_of(smoke_m); _n.clear()
_vo = _n.new('ShaderNodeOutputMaterial'); _pv = _n.new('ShaderNodeVolumePrincipled'); _pv.inputs['Density'].default_value = 4.0
_pv.inputs['Color'].default_value = (0.9, 0.9, 0.92, 1); _l.new(_pv.outputs[0], _vo.inputs['Volume'])
puffs = []
for k in range(3):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.03)
    o = mesh_obj("Smoke%d" % k, bm, [smoke_m], CP); shade_smooth(o); puffs.append(o)
Mm = G_AIM @ Matrix.Translation(MUZ)
flash.matrix_world = Mm @ Matrix.Rotation(R_(90), 4, 'Z')
for f, s_ in ((1, 0.01), (F_FIRE, 0.01), (F_FIRE + 1, 1.6), (F_FIRE + 4, 1.0), (F_FIRE + 8, 0.01)):
    flash.scale = (s_,) * 3; flash.keyframe_insert("scale", frame=f)
key_vis(flash, 1, False); key_vis(flash, F_FIRE + 1, True); key_vis(flash, F_FIRE + 9, False)
fwdg = (G_AIM.to_3x3() @ V(0, -1, 0)).normalized()
for k, o in enumerate(puffs):
    p0 = Mm.translation + fwdg * (0.02 + 0.05 * k); rnd = random.Random(k)
    p1 = p0 + fwdg * (0.15 + 0.08 * k) + V(rnd.uniform(-0.08, 0.08), rnd.uniform(-0.08, 0.08), 0.12 + 0.05 * k)
    for f, s_, p in ((F_FIRE + 1, 0.2, p0), (F_FIRE + 10, 0.55 + 0.1 * k, p0.lerp(p1, 0.5)), (F_FIRE + 30, 0.9 + 0.1 * k, p1)):
        o.location = p; o.scale = (s_,) * 3; o.keyframe_insert("location", frame=f); o.keyframe_insert("scale", frame=f)
    key_vis(o, 1, False); key_vis(o, F_FIRE + 1, True); key_vis(o, F_FIRE + 31, False)

# =========================================================================== cameras (one per shot, hard cuts)
CAMS = coll("Cameras")
def camera(shot, keys, lens=35, fstop=None):
    """keys: [(offset, loc, target)] offsets in frames from the shot start (negative = from the end)"""
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
    return co

def frame_pts(pts, view, lens, fill=0.7, push=0.0):
    """camera location + target that fit `pts` (world) in a 9:16 frame looking along `view`"""
    v = view.normalized(); r = v.cross(V(0, 0, 1)).normalized(); u = r.cross(v)
    c = sum(pts, V(0, 0, 0)) / len(pts)
    tx = 10.125 / lens; ty = 18.0 / lens
    d = 0.0
    for p in pts:
        q = p - c; x, y, z = q.dot(r), q.dot(u), q.dot(v)
        d = max(d, abs(x) / (tx * fill) - z, abs(y) / (ty * fill) - z)
    d = max(d, 0.3) - push
    return c - v * d, c
sc.frame_set(F_FIRE - 40)
hP = P.world_bone("head").translation
gM = G_AIM.translation; gHead = G.world_bone("head", ST["S02"] + 20).translation
fw = fwd_c; side = Rc @ V(1, 0, 0)
shG = G.world_bone("upperarm01.R", ST["S01"] + 120).translation
camera("S01", [(0, shG - fw * 0.50 - side * 0.42 + V(0, 0, 0.14), hP + fw * 2.5 + V(0, 0, -0.55)),
               (-1, gM - fw * 0.60 - side * 0.62 + V(0, 0, 0.20), hP * 0.35 + gM * 0.65 + V(0, 0, 0.02))], lens=24)
camera("S02", [(0, gHead + side * -2.0 + fw * 0.9 + V(0, 0, -0.1), gHead + fw * 0.55 + V(0, 0, -0.3)),
               (-1, gHead + side * -1.85 + fw * 0.85 + V(0, 0, -0.08), gHead + fw * 0.6 + V(0, 0, -0.28))], lens=20)
shL = G.world_bone("upperarm01.L", ST["S03"]).translation
_wr = G.world_bone("wrist.R", F_FIRE - 40).translation; _hat = hP + V(0, 0, 0.32)
_c0, _t0 = frame_pts([G_AIM @ MUZ, _wr, _hat, hP + fw * 1.2 + V(0, 0, -0.6)], fw + side * 0.35 + V(0, 0, -0.22), 24, fill=0.8)
_c1, _t1 = frame_pts([G_AIM @ MUZ, _wr, _hat, hP + fw * 1.2 + V(0, 0, -0.6)], fw + side * 0.35 + V(0, 0, -0.22), 24, fill=0.8, push=0.08)
camera("S03", [(0, _c0, _t0), (-1, _c1, _t1)], lens=24)
print("S03 cam", tuple(round(x, 2) for x in _c0), "dist to gunman head", round((_c0 - G.world_bone("head").translation).length, 2))
gH4 = G.world_bone("head", ST["S04"] + 30).translation
camera("S04", [(0, gH4 + fw * 0.85 + side * 0.65 + V(0, 0, -0.05), gH4 + V(0, 0, -0.02)),
               (-1, gH4 + fw * 0.72 + side * 0.55 + V(0, 0, -0.04), gH4 + V(0, 0, -0.02))], lens=40)
mid5 = gM * 0.55 + hP * 0.45
_t5 = hP * 0.35 + gM * 0.65 + V(0, 0, 0.02)
camera("S05", [(0, gM - fw * 0.70 - side * 0.70 + V(0, 0, 0.22), _t5), (-1, gM - fw * 0.64 - side * 0.66 + V(0, 0, 0.21), _t5)], lens=34)
camera("S06", [(0, V(BX0 + 0.45, BY0 + 0.35, BZ + 1.55), V(GPOS.x, GPOS.y, BZ + 1.15)), (-1, V(BX0 + 0.55, BY0 + 0.35, BZ + 1.55), V(ledge_stand.x, ledge_stand.y, BZ + 1.15))], lens=30)
camera("S07", [(0, V(BX0 - 3.6, -0.6, 1.3), V(BX0, -1.6, BZ + 1.6)), (-1, V(BX0 - 3.7, -0.7, 1.2), V(BX0 - 0.7, -1.7, BZ + 0.4))], lens=26)
camera("S08", [(0, LAND_P + V(-3.0, -1.6, 1.0), LAND_P + V(0, 0, 0.9)), (-1, LAND_P + V(-2.6, -1.5, 0.75), LAND_P + V(0, 0, 0.6))], lens=26)
sc.frame_set(ST["S09"] + 20)
_kn = G.world_bone("lowerleg01.L").translation; _ft = G.world_bone("foot.L").translation; _hd = G.world_bone("wrist.L").translation
_pts9 = [_kn + V(0, 0, 0.12), _ft, _hd, crack.location, G.world_bone("lowerleg01.R").translation, G.world_bone("head").translation + V(0, 0, 0.18)]
_c0, _t0 = frame_pts(_pts9, V(0.15, -1.0, -0.35), 30, fill=0.6)
_c1, _t1 = frame_pts(_pts9, V(0.15, -1.0, -0.35), 30, fill=0.6, push=0.12)
camera("S09", [(0, _c0, _t0), (-1, _c1, _t1)], lens=30)
fl9 = bpy.data.lights.new("S09Fill", 'AREA'); fl9.size = 1.2; fl9.color = (1.0, 0.92, 0.85)
fo9 = bpy.data.objects.new("S09Fill", fl9); CAMS.objects.link(fo9); fo9.location = _c0 + V(0.4, 0.0, 0.6)
fo9.rotation_euler = (_kn - fo9.location).to_track_quat('-Z', 'Y').to_euler()
for f, e in ((1, 0.0), (ST["S09"], 60.0), (SE("S09") + 1, 0.0)):
    fl9.energy = e; fl9.keyframe_insert("energy", frame=f)
for fc in fcurves_of(fl9.animation_data.action):
    for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
fwj = Rj @ V(0, -1, 0)
camera("S10", [(0, LAND_P + fwj * 2.6 + V(0, 0, 1.25), LAND_P + V(0, 0, 0.9)), (-1, LAND_P + fwj * 3.9 + V(0.3, 0, 1.35), limp_end + V(0, 0, 1.1))], lens=28)
camera("S11", [(0, V(100.9, 6.0, 0.9), p11(ST["S11"]) + V(0, 0, 1.5)), (100, V(100.9, -4.5, 0.85), p11(ST["S11"] + 100) + V(0, 0, 1.6)),
               (-1, V(101.2, -16.0, 0.9), p11(SE("S11")) + V(0, 0, 1.5))], lens=26)
rimL = bpy.data.lights.new("HorseRim", 'AREA'); rimL.size = 3.0; rimL.color = (0.7, 0.8, 1.0)
rimO = bpy.data.objects.new("HorseRim", rimL); CAMS.objects.link(rimO); rimO.location = V(96.5, -14.0, 4.0)
rimO.rotation_euler = (V(99.2, -6.0, 1.4) - rimO.location).to_track_quat('-Z', 'Y').to_euler()
for f, e in ((1, 0.0), (ST["S11"], 900.0), (ST["S12"], 0.0)):
    rimL.energy = e; rimL.keyframe_insert("energy", frame=f)
for fc in fcurves_of(rimL.animation_data.action):
    for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
camera("S12", [(0, V(95.0, 2.5, 1.55), V(104.0, 14.0, 1.9)), (-1, V(95.2, 0.5, 1.55), V(104.0, -3.0, 1.9))], lens=26)
camera("S13", [(0, V(100.4, 3.0, 0.75), V(100.6, 13.0, 1.5)), (-1, V(100.4, -0.5, 0.85), V(100.5, 8.0, 1.5))], lens=24)
camera("S14", [(0, V(X1 + 0.5, -9.6, 1.7), V(X1 + 1.2, 2.5, 0.9)), (-1, V(X1 + 0.5, -8.8, 1.65), V(X1 + 1.2, 2.5, 1.2))], lens=36)
camera("S15", [(0, V(X1 + 0.6, 0.55, 1.15), V(X1 + 1.25, 2.3, 1.55)), (-1, V(X1 + 0.55, 0.75, 1.2), V(X1 + 1.25, 2.3, 1.75))], lens=30)
sc.camera = bpy.data.objects["CAM_S01"]

# =========================================================================== look: AgX Punchy, per-set world + exposure (constant keys)
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'
sc.render.use_motion_blur = False
w = bpy.data.worlds.new("B04World"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']
SETS = {"theatre": ((0.20, 0.16, 0.14), 1.0, 0.3), "street": ((0.05, 0.08, 0.22), 1.0, 0.9), "barn": ((0.10, 0.08, 0.10), 1.0, 0.2)}
SHOT_SET = {s: ("theatre" if int(s[1:]) <= 10 else "street" if int(s[1:]) <= 13 else "barn") for s, _ in SHOT_LEN}
for s, _ in SHOT_LEN:
    col, stren, ex = SETS[SHOT_SET[s]]
    bg.inputs[0].default_value = (*col, 1); bg.inputs[1].default_value = stren
    bg.inputs[0].keyframe_insert("default_value", frame=ST[s]); bg.inputs[1].keyframe_insert("default_value", frame=ST[s])
    sc.view_settings.exposure = ex; sc.view_settings.keyframe_insert("exposure", frame=ST[s])
for idb in (w.node_tree, sc):
    ad = idb.animation_data
    if ad and ad.action:
        for fc in fcurves_of(ad.action):
            for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
sc.render.fps = 60
import json
sc["SHOTS_JSON"] = json.dumps([[s, ST[s], SE(s)] for s, _ in SHOT_LEN])
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ANIM_DONE frames", sc.frame_start, sc.frame_end)
