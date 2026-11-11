"""Character + prop animation for SurgeonBrandsLivers (base timing = beat table targets, 60 fps, frames 1-1710).
blender -b scene.blend --python 03_animate.py -- <out.blend>"""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion, Euler, noise

HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib.py")).read())
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
random.seed(11)
V = lambda *a: Vector(a)
TABLE_TOP = 0.95
WIN = V(-0.28, -0.06)
DAIS_H = 0.4
SZ = -6.0

# ------------------------------------------------------------------ ground: floors at 0, hearing dais at DAIS_H
def ground_z(x, y):
    if -12.0 < x < -9.4 and -3.2 < y < 3.2:
        return DAIS_H
    return 0.0

def body_h(x, y):
    u = (x + 0.15) / 0.75; v = y / 0.36
    torso = 0.21 * max(0.0, 1 - u * u) ** 0.5 * max(0.0, 1 - v ** 4) if abs(u) < 1 else 0.0
    legs = 0.14 * max(0.0, 1 - (y / 0.3) ** 2) if 0.4 < x < 1.15 else 0.0
    return max(torso, legs)
def skin_z(x, y):
    return TABLE_TOP + 0.012 + body_h(x, y)

# ------------------------------------------------------------------ actor wrapper around anim_lib's Human + IK rig
class Actor:
    def __init__(self, name):
        self.o = bpy.data.objects[name]
        self.R = make_human_ctrl(self.o)
        self.H = Human(self.R)
        B = self.R.BN
        self.ROOT = B["root"].head_local.copy()
        self.SH = {s: B["upperarm01." + s].head_local.copy() for s in "LR"}
        self.REST_HAND = {}
        for s in "LR":
            wv = B["wrist." + s].head_local
            d = B["finger3-1." + s].head_local - wv
            a = B["finger2-1." + s].head_local - B["finger5-1." + s].head_local
            n = d.cross(a) if s == "L" else a.cross(d)
            self.REST_HAND[s] = self.basis(s, d, n)
        self.poses = []
        self.ik = [c for pb in self.o.pose.bones for c in pb.constraints if c.type == 'IK']
        for pb in self.o.pose.bones:
            pb.rotation_mode = 'QUATERNION'
    @staticmethod
    def basis(s, d, n):
        d = d.normalized(); n = (n - d * n.dot(d)).normalized()
        a = d.cross(n) if s == "R" else n.cross(d)
        return Matrix((d, a, n)).transposed()
    def hand_matrix(self, s, W, d, n):
        Rm = self.basis(s, d, n) @ self.REST_HAND[s].transposed()
        wr = self.R.BN["wrist." + s].head_local
        return Matrix.Translation(W) @ Rm.to_4x4() @ Matrix.Translation(-wr) @ self.R.rest("IK_hand." + s)
    def arm_rest(self, s, fwd=0.0, out=8.0, L=0.47, bend=0.0):
        sx = 1 if s == "L" else -1
        R = Matrix.Rotation(R_(-fwd), 3, 'X') @ Matrix.Rotation(R_(sx * out), 3, 'Y')
        W = self.SH[s] + V(sx * 0.04, -0.02, 0) + R @ V(0, 0, -L * (1 - bend))
        if bend:
            W += V(0, -L * bend * 0.9, L * bend * 0.4)
        d = R @ V(sx * 0.05, -0.15, -1.0)
        n = R @ V(-sx * 0.9, 0.35, 0.0)
        return W, d, n
    # P(frame, pos, yaw, ...) collects a pose; bake() keys them all (body first, then hands relative to the body)
    def P(self, f, pos, yaw=0.0, pitch=0.0, roll=0.0, spine=(0, 0, 0), head=(0, 0, 0), feet=None, hands=None, curl=None, face=None, legs_fk=None):
        self.poses.append((f, dict(pos=Vector(pos), yaw=yaw, pitch=pitch, roll=roll, spine=spine, head=head,
                                   feet=feet, hands=hands or {}, curl=curl or {}, face=face or {}, legs_fk=legs_fk)))
    def stance(self, pos, yaw, width=1.0):
        return {s: (self.H.foot_xy(s, Vector(pos), yaw) - Vector(pos).to_2d()) * width + Vector(pos).to_2d() for s in "LR"}
    def key_body(self, f, p):
        Rw = Matrix.Rotation(R_(p["yaw"]), 3, 'Z') @ Matrix.Rotation(R_(p["pitch"]), 3, 'X') @ Matrix.Rotation(R_(p["roll"]), 3, 'Y')
        M = Matrix.Translation(p["pos"]) @ Rw.to_4x4() @ Matrix.Translation(-self.ROOT) @ self.R.rest("root")
        self.R.key_world("root", f, M)
        fl, sd, tw = p["spine"]
        for n, w in Human.SPINE_W.items():
            self.R.key_rot(n, f, [("X", fl * w), ("Y", sd * w), ("Z", tw * w)])
        hp, ht, hr = p["head"]
        for n, w in Human.HEAD_W.items():
            self.R.key_rot(n, f, [("X", hp * w), ("Y", hr * w), ("Z", ht * w)])
        for s in "LR":
            c = p["curl"].get(s, (22, 18))
            self.key_fingers(s, f, c[0], c[1])
        self.key_face(f, p["face"])
    def key_fingers(self, s, f, curl, thumb=18):
        Rh = self.REST_HAND[s]; d, a = Rh.col[0].copy(), Rh.col[1].copy(); sign = 1 if s == "R" else -1
        JW = (0.8, 1.1, 0.8)
        for k in range(2, 6):
            c = curl[k - 2] if isinstance(curl, (list, tuple)) else curl
            for j in range(1, 4):
                b = "finger%d-%d.%s" % (k, j, s)
                self.R.key_q(b, f, self.R.local_q(b, Matrix.Rotation(R_(c * JW[j - 1] * sign), 3, a)))
        for j, fl in ((1, thumb * 0.4), (2, thumb * 0.8), (3, thumb)):
            b = "finger1-%d.%s" % (j, s)
            self.R.key_q(b, f, self.R.local_q(b, Matrix.Rotation(R_(fl * sign), 3, a) @ Matrix.Rotation(R_(22 * sign), 3, d)))
    def key_face(self, f, fc):
        PB = self.R.PB
        sm, wide, brow, jaw, close = fc.get("smile", 0), fc.get("wide", 0.3), fc.get("brow", 0), fc.get("jaw", 0), fc.get("close", 0)
        for s in "LR":
            sx = 1 if s == "L" else -1
            for n in ("risorius02.", "risorius03."):
                pb = PB[n + s]; pb.location = V(0.010 * sm * sx, 0, 0.008 * sm); pb.keyframe_insert("location", frame=f, group=n + s)
            pb = PB["orbicularis03." + s]; pb.rotation_quaternion = Quaternion((1, 0, 0), R_(25 * wide - 32 * close))
            pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
            pb = PB["orbicularis04." + s]; pb.rotation_quaternion = Quaternion((1, 0, 0), R_(-25 * wide + 8 * close))
            pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
            for n in ("oculi01.", "oculi02."):
                pb = PB[n + s]; pb.rotation_quaternion = Quaternion((1, 0, 0), R_(20 * brow)); pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
        pb = PB["jaw"]; pb.rotation_quaternion = Quaternion((1, 0, 0), R_(jaw)); pb.keyframe_insert("rotation_quaternion", frame=f, group="jaw")
    def key_feet(self, f, p):
        ft = p["feet"]
        if ft == "body":     # feet follow the body (lying / carried): rest positions through the root transform
            ev(f); M = self.R.delta("root")
            for s in "LR":
                n = "IK_foot." + s
                self.R.key_world(n, f, M @ self.R.rest(n))
                pn = "Pole_knee." + s
                pole = M @ (self.R.BN["lowerleg01." + s].head_local + V(0, -0.6, 0))
                pb = self.R.PB[pn]; pb.location = self.R.rest(pn).to_3x3().inverted() @ (pole - self.R.BN[pn].head_local)
                pb.keyframe_insert("location", frame=f, group=pn)
            return
        for s in "LR":
            spec = ft[s]
            if len(spec) == 2:
                xy, yw = spec; lift = 0.0; pitch = 0.0
            else:
                xy, yw, lift, pitch = spec
            self.H.key_foot(s, f, Vector(xy), yw, lift, pitch)
    def key_hands(self, f, p):
        ev(f)
        M = self.R.delta("spine01"); R3 = M.to_3x3()
        for s in "LR":
            sx = 1 if s == "L" else -1
            kind, prm = p["hands"].get(s, ("rest", {}))
            if kind == "world":
                W, d, n = prm
                self.R.key_world("IK_hand." + s, f, self.hand_matrix(s, W, d, n))
            elif kind == "body":       # rest-body coordinates
                W, d, n = prm
                self.R.key_world("IK_hand." + s, f, self.hand_matrix(s, M @ W, R3 @ d, R3 @ n))
            elif kind == "fn":
                W, d, n = prm(f)
                self.R.key_world("IK_hand." + s, f, self.hand_matrix(s, W, d, n))
            else:
                W, d, n = self.arm_rest(s, **prm)
                self.R.key_world("IK_hand." + s, f, self.hand_matrix(s, M @ W, R3 @ d, R3 @ n))
            pole = M @ (self.SH[s] + V(0.35 * sx, 0.45, -0.25))
            pn = "Pole_elbow." + s; pb = self.R.PB[pn]
            pb.location = self.R.rest(pn).to_3x3().inverted() @ (pole - self.R.BN[pn].head_local)
            pb.keyframe_insert("location", frame=f, group=pn)
    def bake(self):
        self.poses.sort(key=lambda x: x[0])
        for f, p in self.poses:
            self.key_body(f, p)
        for f, p in self.poses:
            self.key_feet(f, p)
        for f, p in self.poses:
            self.key_hands(f, p)
    def world(self, f, bone, local=V(0, 0, 0)):
        ev(f); pb = self.R.PB[bone]
        return self.o.matrix_world @ (pb.matrix @ local)
    def child_of_bone(self, ob, bone):
        """parent ob to a pose bone keeping its current world transform (rest pose)"""
        bn = self.R.BN[bone]
        ob.parent = self.o; ob.parent_type = 'BONE'; ob.parent_bone = bone
        ob.matrix_parent_inverse = (bn.matrix_local @ Matrix.Translation(V(0, bn.length, 0))).inverted()

def stepped(id_, frames):
    for fc in fcurves(id_):
        for kp in fc.keyframe_points:
            if int(round(kp.co.x)) in frames:
                kp.interpolation = 'CONSTANT'

def vis(names_or_obs, ranges):
    obs = [bpy.data.objects[n] if isinstance(n, str) else n for n in names_or_obs]
    key_vis(obs, ranges)

def part(rig, suffix):
    return [c for c in bpy.data.objects[rig].children if c.name.split(".")[-1] == suffix]

S1, PT, S2, NU, GH = Actor("Surgeon1"), Actor("Patient"), Actor("Surgeon2"), Actor("Nurse"), Actor("GloveHands")
AN = Actor("Anaesth")
PA, PBn, PC = Actor("PanelA"), Actor("PanelB"), Actor("PanelC")

# ------------------------------------------------------------------ caps + masks (fitted to each head)
M_CAP = mat("SurgCap", (0.2, 0.42, 0.55), 0.85); M_CAP.node_tree.nodes["Principled BSDF"].inputs['Sheen Weight'].default_value = 0.6
M_CAP2 = mat("SurgCap2", (0.45, 0.3, 0.55), 0.85)
def head_box(act):
    body = bpy.data.objects[act.o.name + ".body"]
    gi = body.vertex_groups["head"].index
    pts = [v.co for v in body.data.vertices if any(g.group == gi and g.weight > 0.6 for g in v.groups)]
    mn = V(*[min(p[i] for p in pts) for i in range(3)]); mx = V(*[max(p[i] for p in pts) for i in range(3)])
    return mn, mx
def landmarks(act):
    B = act.R.BN
    return B["eye.L"].head_local.copy(), B["head"].tail_local.copy(), B["jaw"].tail_local.copy(), B["head"].length / 0.158
def face_fit(act):
    """measure the evaluated head mesh (rest pose): nose-tip y, cheek half-width, skull top, forehead front, back of head"""
    eye, top, chin, k = landmarks(act)
    body = bpy.data.objects[act.o.name + ".body"]
    dg = bpy.context.evaluated_depsgraph_get(); me = body.evaluated_get(dg).to_mesh()
    P = [body.matrix_world @ v.co for v in me.vertices if v.co.z > chin.z - 0.03 and abs(v.co.x) < 0.13 and v.co.y < eye.y + 0.26]
    body.evaluated_get(dg).to_mesh_clear()
    lower = [p for p in P if chin.z - 0.015 < p.z < eye.z - 0.02]
    front = min(p.y for p in lower if abs(p.x) < 0.02)
    cheek = max(abs(p.x) for p in lower if p.y < eye.y + 0.05)
    skull = [p for p in P if p.z > eye.z + 0.02]
    topz = max(p.z for p in skull); fh = min(p.y for p in skull if abs(p.x) < 0.03); back = max(p.y for p in skull)
    hw = max(abs(p.x) for p in skull)
    return dict(front=front, cheek=cheek, top=topz, fh=fh, back=back, hw=hw, eye=eye, chin=chin)
def make_cap(act, m):
    F = face_fit(act); eye = F["eye"]
    cz = eye.z + 0.038; rz = (F["top"] - cz) * 1.08 + 0.014
    c_ = V(0, (F["fh"] + F["back"]) / 2 - 0.004, cz); ry = (F["back"] - F["fh"]) / 2 + 0.016; rx = F["hw"] + 0.012
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=36, v_segments=18, radius=1.0)
    for v in list(bm.verts):
        if v.co.z < -0.05 - 0.8 * max(0.0, v.co.y): bm.verts.remove(v)
    for v in bm.verts:
        v.co = V(v.co.x * rx, v.co.y * ry, v.co.z * rz + 0.003 * math.sin(v.co.x * 40) * math.cos(v.co.y * 30))
    me = bpy.data.meshes.new("Cap"); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    cap = bpy.data.objects.new(act.o.name + "_Cap", me); bpy.data.collections["People"].objects.link(cap); me.materials.append(m)
    cap.location = c_
    cap.modifiers.new("t", 'SOLIDIFY').thickness = 0.003
    act.child_of_bone(cap, "head")
    return cap
M_MASK = mat("MaskFabric", (0.32, 0.55, 0.75), 0.85)
M_MASK.node_tree.nodes["Principled BSDF"].inputs['Sheen Weight'].default_value = 0.5
def make_mask(act):
    """pleated surgical mask wrapped round the lower face; origin on the ear line so it can be pulled down"""
    F = face_fit(act); eye, chin = F["eye"], F["chin"]; k = 1.0
    z0, z1 = chin.z - 0.022, eye.z - 0.016; H = z1 - z0; zc = (z0 + z1) / 2
    r = max(0.07, F["cheek"] * 1.06); ay = F["front"] + r + 0.002
    bm = bmesh.new(); NA, NZ = 28, 16; vv = {}
    for i in range(NA + 1):
        a_ = R_(-80 + 160 * i / NA)
        for j in range(NZ + 1):
            z = z0 + H * j / NZ; u = (z - zc) / (H / 2)
            rr = r + 0.008 * math.cos(a_) ** 2 * (1 - u * u) + 0.0018 * math.sin(j * math.pi / 2.7)
            if j in (0, NZ): rr -= 0.004
            vv[i, j] = bm.verts.new((rr * math.sin(a_), ay - rr * math.cos(a_), z))
    for i in range(NA):
        for j in range(NZ):
            bm.faces.new((vv[i, j], vv[i + 1, j], vv[i + 1, j + 1], vv[i, j + 1]))
    me = bpy.data.meshes.new("Mask"); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    piv = V(0, ay + 0.01, eye.z - 0.035)
    me.transform(Matrix.Translation(-piv))
    mk = bpy.data.objects.new(act.o.name + "_Mask", me); bpy.data.collections["People"].objects.link(mk); me.materials.append(M_MASK)
    mk.modifiers.new("t", 'SOLIDIFY').thickness = 0.0015
    mk.location = piv
    # ear loops
    for sx in (-1, 1):
        cu = bpy.data.curves.new("EarLoop", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0012
        sp = cu.splines.new('BEZIER'); sp.bezier_points.add(2)
        a_ = R_(78 * sx)
        p0 = V(r * math.sin(a_), ay - r * math.cos(a_), z1 - 0.01) - piv
        p2 = V(r * math.sin(a_), ay - r * math.cos(a_), z0 + 0.01) - piv
        p1 = V(sx * (F["hw"] + 0.004), F["front"] + 0.13, eye.z - 0.03) - piv
        for bp, co in zip(sp.bezier_points, (p0, p1, p2)):
            bp.co = co; bp.handle_left_type = bp.handle_right_type = 'AUTO'
        lo = bpy.data.objects.new("EarLoop", cu); bpy.data.collections["People"].objects.link(lo); cu.materials.append(M_MASK)
        lo.parent = mk
    act.child_of_bone(mk, "head")
    return mk
# gloves: hand faces get a nitrile material slot (S1's turn back to skin tone for the hearing)
def gloves(act, off_at=None):
    """hand faces get a copy of the skin material with a nitrile layer mixed over it (S1's comes off for the hearing)"""
    body = bpy.data.objects[act.o.name + ".body"]
    gm = body.data.materials[0].copy(); gm.name = "Glove_" + act.o.name
    nt = gm.node_tree; out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output] or [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL']
    out = out[0]; src = out.inputs['Surface'].links[0].from_socket
    gp = nt.nodes.new('ShaderNodeBsdfPrincipled'); gp.inputs['Base Color'].default_value = (0.50, 0.68, 0.88, 1)
    gp.inputs['Roughness'].default_value = 0.38; gp.inputs['Coat Weight'].default_value = 0.25; gp.inputs['Subsurface Weight'].default_value = 0.15
    mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = 1.0
    nt.links.new(src, mx.inputs[1]); nt.links.new(gp.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    if off_at:
        for f, v in ((1, 1.0), (off_at, 1.0), (off_at + 1, 0.0)):
            mx.inputs['Fac'].default_value = v; mx.inputs['Fac'].keyframe_insert("default_value", frame=f)
        for fc in fcurves(nt):
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
    body.data.materials.append(gm); slot = len(body.data.materials) - 1
    idx = {g.index: g.name for g in body.vertex_groups}
    hand = set()
    for v in body.data.vertices:
        if sum(g.weight for g in v.groups if idx.get(g.group, "").startswith(("wrist", "finger", "metacarpal"))) > 0.5:
            hand.add(v.index)
    for p in body.data.polygons:
        if all(i in hand for i in p.vertices):
            p.material_index = slot
gloves(S1, 1100); gloves(S2); gloves(NU); gloves(AN)
CAPS = {a.o.name: make_cap(a, M_CAP if a is not S2 else M_CAP2) for a in (S1, S2, NU, AN)}
MASKS = {a.o.name: make_mask(a) for a in (S1, S2, NU, AN)}

# ================================================================== SURGEON 1
s1_or = V(-0.25, -0.66, S1.ROOT.z - 0.03); Y1 = 180
ST1 = S1.stance(s1_or, Y1, 1.15)
F1 = {s: (ST1[s], Y1) for s in "LR"}
pen_or = bpy.data.objects["ArgonPen_OR"]; drv = bpy.data.objects["NeedleDriver"]
def tool_hand(tool, grip=0.07):
    """hand target from a tool held like a pen: wrist behind the grip, fingers along the shaft"""
    def fn(f):
        ev(f); M = tool.matrix_world; ax = (M.to_3x3() @ V(0, 0, 1)).normalized()
        g = M @ V(0, 0, grip)
        side = ax.cross(V(0, 0, 1)).normalized() if abs(ax.z) < 0.95 else V(1, 0, 0)
        W = g + ax * 0.075 + side * 0.012
        d = (-ax * 0.8 + V(0, 0, -0.2)).normalized()
        n = (-side).normalized()
        return W, d, n
    return fn
# pen animation in the OR (mirrors the studio writing): hover, descend, small writing loops, lift away
def key_tool(ob, f, loc, ax):
    ob.location = loc; ob.rotation_euler = V(0, 0, 1).rotation_difference(ax.normalized()).to_euler()
    ob.keyframe_insert("location", frame=f); ob.keyframe_insert("rotation_euler", frame=f)
AXP = V(0.25, -0.75, 0.9)        # pen leans back toward the surgeon
skin_w = skin_z(WIN.x, WIN.y)
key_tool(pen_or, 1, V(WIN.x + 0.02, WIN.y - 0.06, skin_w + 0.10), AXP)
key_tool(pen_or, 40, V(WIN.x + 0.01, WIN.y - 0.03, skin_w + 0.05), AXP)
key_tool(pen_or, 80, V(WIN.x - 0.01, WIN.y, skin_w + 0.012), AXP)
for i, f in enumerate(range(95, 300, 14)):
    a = i * 1.3
    key_tool(pen_or, f, V(WIN.x - 0.02 + 0.018 * math.sin(a), WIN.y + 0.012 * math.cos(a), skin_w + 0.012), AXP)
key_tool(pen_or, 300, V(WIN.x + 0.05, WIN.y - 0.12, skin_w + 0.12), AXP)
key_tool(pen_or, 318, V(0.33, -1.0, 1.04), V(1, 0.3, 0.05))         # put down on the tray before stitching
key_tool(pen_or, 1710, V(0.33, -1.0, 1.04), V(1, 0.3, 0.05))
# needle driver: picked up from the tray, stitches, put back
DRV_REST = V(0.28, -0.92, 1.04)
key_tool(drv, 1, DRV_REST, V(1, -0.2, 0.05)); key_tool(drv, 318, DRV_REST, V(1, -0.2, 0.05))
inc = [WIN.lerp(WIN + V(0.0, 0.0), 0)]
INC0, INC1 = V(WIN.x - 0.11, WIN.y + 0.01), V(WIN.x + 0.11, WIN.y - 0.01)
ST_F = []
for k in range(9):
    f0 = 328 + k * 11
    p = INC0.lerp(INC1, (k + 0.5) / 9)
    key_tool(drv, f0, V(p.x, p.y + 0.02, skin_z(p.x, p.y) + 0.035), V(0.1, -0.7, 1.0))
    key_tool(drv, f0 + 4, V(p.x, p.y - 0.005, skin_z(p.x, p.y) + 0.008), V(0.1, -0.5, 1.0))
    key_tool(drv, f0 + 8, V(p.x + 0.004, p.y - 0.02, skin_z(p.x, p.y) + 0.05), V(0.2, -0.9, 0.8))
    ST_F.append(f0 + 5)
key_tool(drv, 446, DRV_REST + V(0, 0, 0.04), V(1, -0.2, 0.3)); key_tool(drv, 458, DRV_REST, V(1, -0.2, 0.05)); key_tool(drv, 1710, DRV_REST, V(1, -0.2, 0.05))
for k, so_ in enumerate(bpy.data.objects[n] for n in sorted(o.name for o in bpy.data.objects if o.name.startswith("Suture_"))):
    key_vis([so_], [(ST_F[k], 1710)])
# S1 body poses in the OR
mask1 = MASKS["Surgeon1"]
def maskrot(ob, f, deg):
    ob.rotation_euler = (ob.rotation_euler.x, ob.rotation_euler.y, ob.rotation_euler.z)
    ob["down"] = deg
lean = (24, 0, 0)
S1.P(1, s1_or + V(0, 0.02, -0.02), Y1, spine=(24, 0, -4), head=(22, -4, 0), feet=F1,
     hands={"R": ("fn", tool_hand(pen_or)), "L": ("world", (V(-0.50, -0.34, skin_z(-0.50, -0.3) + 0.03), V(0.2, 1, -0.6), V(0, 0, -1)))},
     curl={"R": (55, 40), "L": (18, 14)})
for f in (60, 110, 160, 210, 260):
    S1.P(f, s1_or + V(0.01 * math.sin(f / 30), 0.03, -0.03), Y1, spine=(27, 2 * math.sin(f / 40), -4), head=(24, -6, 2), feet=F1,
         hands={"R": ("fn", tool_hand(pen_or)), "L": ("world", (V(-0.50, -0.34, skin_z(-0.50, -0.3) + 0.03), V(0.2, 1, -0.6), V(0, 0, -1)))},
         curl={"R": (55, 40), "L": (18, 14)})
S1.P(300, s1_or + V(0.04, 0.02, -0.02), Y1 + 8, spine=(22, 0, 8), head=(20, -2, 0), feet=F1,
     hands={"R": ("fn", tool_hand(pen_or)), "L": ("world", (V(-0.50, -0.34, skin_z(-0.50, -0.3) + 0.03), V(0.2, 1, -0.6), V(0, 0, -1)))}, curl={"R": (55, 40)})
S1.P(318, s1_or + V(0.08, 0.0, -0.02), Y1 + 20, spine=(18, 0, 18), head=(20, 10, 0), feet=F1,
     hands={"R": ("fn", tool_hand(drv, 0.115)), "L": ("world", (V(-0.50, -0.34, skin_z(-0.50, -0.3) + 0.03), V(0.2, 1, -0.6), V(0, 0, -1)))}, curl={"R": (60, 45)})
for f in range(332, 430, 16):
    S1.P(f, s1_or + V(0.01, 0.04, -0.03), Y1, spine=(28, 0, -2), head=(26, -4, 0), feet=F1,
         hands={"R": ("fn", tool_hand(drv, 0.115)), "L": ("world", (V(WIN.x - 0.04, WIN.y - 0.1, skin_w + 0.03), V(0.4, 1, -0.5), V(0, 0, -1)))},
         curl={"R": (60, 45), "L": (30, 25)})
S1.P(432, s1_or + V(0.05, 0.01, -0.02), Y1 + 12, spine=(22, 0, 10), head=(22, 8, 0), feet=F1,
     hands={"R": ("fn", tool_hand(drv, 0.115))}, curl={"R": (60, 45)})
S1.P(437, s1_or + V(0.07, 0.0, -0.02), Y1 + 18, spine=(18, 0, 16), head=(20, 12, 0), feet=F1,
     hands={"R": ("fn", tool_hand(drv, 0.115))}, curl={"R": (60, 45)})
S1.P(446, s1_or + V(0.08, 0.0, -0.02), Y1 + 22, spine=(16, 0, 20), head=(18, 14, 0), feet=F1,
     hands={"R": ("fn", tool_hand(drv, 0.115))}, curl={"R": (60, 45)})
S1.P(458, s1_or + V(0.08, 0.0, -0.02), Y1 + 22, spine=(16, 0, 20), head=(18, 14, 0), feet=F1,
     hands={"R": ("fn", tool_hand(drv, 0.115))}, curl={"R": (30, 20)})
def mask_edge_hand(f):
    ev(f); M = mask1.matrix_world
    W = M @ V(0, -0.11, -0.06)          # chin edge of the mask, in front
    return W, (M.to_3x3() @ V(0, 0.2, 1)).normalized(), (M.to_3x3() @ V(0, 1, 0)).normalized()
S1.P(478, s1_or + V(0.02, -0.02, 0.0), Y1 + 6, spine=(6, 0, 4), head=(4, 4, 0), feet=F1,
     hands={"R": ("fn", mask_edge_hand)}, curl={"R": (45, 35)})
S1.P(500, s1_or + V(0.0, -0.03, 0.01), Y1 + 4, spine=(2, 0, 2), head=(-4, 6, 4), feet=F1,
     hands={"R": ("fn", mask_edge_hand)}, curl={"R": (45, 35)}, face={"smile": 0.3})
S1.P(520, s1_or + V(0.0, -0.03, 0.01), Y1 + 4, spine=(0, -3, 2), head=(-8, 8, 6), feet=F1,
     hands={"R": ("rest", dict(fwd=12, out=12, bend=0.2))}, face={"smile": 1.2, "brow": -0.2, "wide": 0.1, "close": 0.2})
for f, hd in ((545, (-6, 5, 8)), (575, (-9, 2, 4)), (600, (-7, 4, 6))):
    S1.P(f, s1_or + V(0.0, -0.03, 0.01), Y1 + 4, spine=(0, -3, 2), head=hd, feet=F1,
         hands={"R": ("rest", dict(fwd=8, out=10, bend=0.15)), "L": ("rest", dict(fwd=6, out=8))}, face={"smile": 1.3, "brow": -0.35, "wide": 0.05, "close": 0.3})
mask1.rotation_euler = (0, 0, 0); mask1.keyframe_insert("rotation_euler", frame=478)
mask1.rotation_euler = (R_(80), 0, 0); mask1.keyframe_insert("rotation_euler", frame=500)
# hearing room: in a suit at the lectern, facing the panel (-X)
s1_h = V(-6.72, 0.0, S1.ROOT.z - 0.02); YH = -90
STH = S1.stance(s1_h, YH, 1.1); FH = {s: (STH[s], YH) for s in "LR"}
def lect(s, f):
    W = V(-6.9, 0.2 if s == "L" else -0.2, 1.245)
    return W, V(-1, 0, -0.08), V(0, 0, -1)
S1.P(1200, s1_h, YH, spine=(10, 0, 0), head=(18, 0, 0), feet=FH, hands={"L": ("fn", lambda f: lect("L", f)), "R": ("fn", lambda f: lect("R", f))})
S1.P(1231, s1_h, YH, spine=(12, 0, 0), head=(22, 0, 0), feet=FH, hands={"L": ("fn", lambda f: lect("L", f)), "R": ("fn", lambda f: lect("R", f))}, face={"brow": 0.4})
S1.P(1275, s1_h + V(0, 0, -0.01), YH, spine=(14, 2, 0), head=(26, 4, 0), feet=FH, hands={"L": ("fn", lambda f: lect("L", f)), "R": ("fn", lambda f: lect("R", f))}, face={"brow": 0.5})
def spread(s, up=0.0):
    sx = 1 if s == "L" else -1
    return ("body", (V(sx * 0.3, -0.32, 1.27 + up), V(sx * 0.4, -1, 0.1), V(0, 0, 1)))
S1.P(1310, s1_h + V(0, 0, 0.01), YH, spine=(4, 0, 0), head=(4, 0, 0), feet=FH, hands={"L": spread("L"), "R": spread("R")}, curl={"L": (12, 10), "R": (12, 10)}, face={"brow": -0.3, "jaw": 4})
S1.P(1345, s1_h + V(0, 0, 0.02), YH, spine=(2, 0, 0), head=(0, 0, 3), feet=FH, hands={"L": spread("L", 0.06), "R": spread("R", 0.06)}, curl={"L": (10, 8), "R": (10, 8)}, face={"brow": -0.4, "jaw": 2})
S1.P(1380, s1_h, YH, spine=(6, 0, 0), head=(16, 0, 0), feet=FH, hands={"L": spread("L", -0.04), "R": spread("R", -0.04)}, face={"brow": 0.2})
S1.P(1405, s1_h, YH, spine=(6, 0, 0), head=(-2, 0, 0), feet=FH, hands={"L": spread("L", -0.06), "R": spread("R", -0.06)})
S1.P(1430, s1_h, YH, spine=(8, 0, 0), head=(18, 0, 0), feet=FH, hands={"L": ("fn", lambda f: lect("L", f)), "R": ("fn", lambda f: lect("R", f))}, face={"brow": 0.4})
S1.P(1500, s1_h, YH, spine=(10, 0, 0), head=(10, -6, 0), feet=FH, hands={"L": ("fn", lambda f: lect("L", f)), "R": ("fn", lambda f: lect("R", f))}, face={"brow": 0.5})
S1.P(1540, s1_h + V(0.02, 0, 0.0), YH, spine=(4, 0, 0), head=(0, -4, 0), feet=FH, hands={"L": ("fn", lambda f: lect("L", f)), "R": ("fn", lambda f: lect("R", f))}, face={"wide": 0.4})
S1.P(1548, s1_h + V(0.04, 0, 0.02), YH, spine=(-4, 0, 0), head=(-8, -4, 0), feet=FH, hands={"L": ("fn", lambda f: lect("L", f)), "R": ("fn", lambda f: lect("R", f))}, face={"wide": 0.8})
S1.P(1600, s1_h, YH, spine=(16, 0, 0), head=(26, 0, 0), feet=FH, hands={"L": ("fn", lambda f: lect("L", f)), "R": ("fn", lambda f: lect("R", f))}, face={"close": 1.0, "brow": 0.6})
S1.P(1710, s1_h + V(0, 0, -0.02), YH, spine=(22, 0, 0), head=(32, 0, 0), feet=FH, hands={"L": ("fn", lambda f: lect("L", f)), "R": ("fn", lambda f: lect("R", f))}, face={"close": 1.0, "brow": 0.7})
S1.bake()
stepped(S1.o, {600})
vis(part("Surgeon1", "male_casualsuit01") + [CAPS["Surgeon1"], mask1] + list(mask1.children), [(0, 1100)])
vis(part("Surgeon1", "male_elegantsuit01") + part("Surgeon1", "short02"), [(1101, 1710)])

# ================================================================== PATIENT
pt_lie_on_table = None
def lie(act, f, pos, yaw, arms=8.0, curl=(20, 15)):
    act.P(f, pos, yaw, pitch=-90, feet="body", hands={"L": ("rest", dict(out=arms)), "R": ("rest", dict(out=arms))}, curl={"L": curl, "R": curl})
# find the root position that puts her head beyond the ether screen
pt_pos = V(-0.25, 0.0, TABLE_TOP + 0.10)
lie(PT, 1, pt_pos, 90); lie(PT, 600, pt_pos, 90)
# home: standing with a mug, the pain hits, she doubles over
hp = V(5.95, -0.3, PT.ROOT.z - 0.02); YP = -58
STP = PT.stance(hp, YP); FP = {s: (STP[s], YP) for s in "LR"}
STP2 = dict(STP); STP2["R"] = STP["R"] + V(0.10, -0.12); FP2 = {"L": (STP["L"], YP), "R": (STP2["R"], YP - 15)}
mug = bpy.data.objects["Mug"]
def mug_hand(f):
    ev(f); M = mug.matrix_world; c_ = M @ V(0, 0, 0.05); out = (M.to_3x3() @ V(0, -1, 0)).normalized()
    return c_ + out * 0.048 + V(0, 0, -0.01), (M.to_3x3() @ V(0.0, 1, 0.3)).normalized(), (M.to_3x3() @ V(0, 1, 0)).normalized()
SIDE_R = ("body", (V(-0.185, -0.135, 1.07), V(0.45, -0.35, -0.75), V(0.85, 0.55, 0)))   # palm flat on the outside of her top
PT.P(605, hp, YP, spine=(2, 0, 0), head=(-4, 0, 0), feet=FP, hands={"L": ("fn", mug_hand), "R": ("rest", dict(out=8, fwd=4))}, curl={"L": (55, 40)})
PT.P(640, hp, YP, spine=(0, 0, -4), head=(-8, 6, 0), feet=FP, hands={"L": ("fn", mug_hand), "R": ("rest", dict(out=8, fwd=6))}, curl={"L": (55, 40)}, face={"smile": 0.2})
PT.P(662, hp + V(0, 0, -0.01), YP, spine=(14, 4, 0), head=(6, 0, 0), feet=FP, hands={"L": ("fn", mug_hand), "R": SIDE_R}, curl={"L": (55, 40), "R": (14, 12)}, face={"brow": 0.8, "close": 0.5, "jaw": 4})
PT.P(685, hp + V(0.02, 0, -0.06), YP, pitch=12, spine=(42, 6, 0), head=(14, 0, 0), feet=FP, hands={"L": ("body", (V(0.16, -0.36, 0.72), V(0.1, -0.4, -1), V(0, 1, 0))), "R": SIDE_R}, curl={"L": (15, 12), "R": (14, 12)}, face={"brow": 1.0, "close": 0.7, "jaw": 7})
PT.P(700, hp + V(0.03, -0.02, -0.09), YP - 4, pitch=12, spine=(44, 8, 0), head=(10, 0, 0), feet=FP,
     hands={"L": ("body", (V(0.12, -0.32, 0.62), V(0.1, -0.3, -1), V(0, 1, 0))), "R": SIDE_R}, curl={"L": (10, 10), "R": (14, 12)}, face={"brow": 1.0, "close": 0.8, "jaw": 9})
FPm = {"L": (STP["L"], YP), "R": (STP["R"].lerp(STP2["R"], 0.5), YP - 8, 0.06, 10)}
PT.P(714, hp + V(0.045, -0.04, -0.11), YP - 6, pitch=13, spine=(45, 9, 0), head=(6, -2, 0), feet=FPm,
     hands={"L": ("body", (V(0.13, -0.31, 0.58), V(0.1, -0.3, -1), V(0, 1, 0))), "R": SIDE_R}, curl={"L": (20, 15), "R": (14, 12)}, face={"brow": 1.0, "close": 0.7, "jaw": 9})
PT.P(728, hp + V(0.06, -0.06, -0.12), YP - 8, pitch=15, spine=(46, 10, 0), head=(0, -4, 0), feet=FP2,
     hands={"L": ("body", (V(0.14, -0.30, 0.55), V(0.1, -0.3, -1), V(0, 1, 0))), "R": SIDE_R}, curl={"L": (30, 20), "R": (14, 12)}, face={"brow": 1.0, "close": 0.6, "jaw": 10})
PT.P(760, hp + V(0.06, -0.06, -0.15), YP - 8, pitch=16, spine=(40, 12, 0), head=(-14, -4, 0), feet=FP2,
     hands={"L": ("body", (V(0.14, -0.30, 0.52), V(0.1, -0.3, -1), V(0, 1, 0))), "R": SIDE_R}, curl={"L": (30, 20), "R": (14, 12)}, face={"brow": 1.0, "close": 0.4, "jaw": 12})
PT.P(790, hp + V(0.06, -0.06, -0.17), YP - 8, pitch=17, spine=(44, 12, 0), head=(-10, -4, 0), feet=FP2,
     hands={"L": ("body", (V(0.14, -0.30, 0.50), V(0.1, -0.3, -1), V(0, 1, 0))), "R": SIDE_R}, curl={"L": (30, 20), "R": (14, 12)}, face={"brow": 1.0, "close": 0.7, "jaw": 8})
# mug: in her hand (keys derived from her hand), slips at 690, falls, bounces
def mug_key(f, loc, rot):
    mug.location = loc; mug.rotation_euler = rot; mug.keyframe_insert("location", frame=f); mug.keyframe_insert("rotation_euler", frame=f)
mug_key(1, V(7.1, 0.75, 0.42), (0, 0, 0))
FWD = Matrix.Rotation(R_(YP), 3, 'Z')
def bodyp(x, y, z): return V(hp.x, hp.y, 0) + FWD @ V(x, y, 0) + V(0, 0, z)
mug_key(600, bodyp(0.12, -0.33, 1.05), (0, 0, R_(YP)))
mug_key(630, bodyp(0.12, -0.33, 1.07), (R_(-6), 0, R_(YP)))
mug_key(645, bodyp(0.12, -0.32, 1.08), (0, 0, R_(YP)))
mug_key(662, bodyp(0.12, -0.36, 1.03), (R_(10), 0, R_(YP)))
mug_key(679, bodyp(0.16, -0.48, 0.05), (R_(70), R_(20), R_(YP + 30)))
mug_key(687, bodyp(0.18, -0.56, 0.12), (R_(110), R_(40), R_(YP + 50)))
mug_key(697, bodyp(0.20, -0.62, 0.04), (R_(90), R_(10), R_(YP + 65)))
mug_key(1710, bodyp(0.20, -0.64, 0.04), (R_(90), R_(10), R_(YP + 65)))
# bed ride (lying, feet first), then back on the table
bed_root = bpy.data.objects.new("BedRig", None); bpy.data.collections["OR_Set"].objects.link(bed_root)
bed = import_glb("/opt/assets/sbl/objv/bed.glb", "HospitalBed", length=2.1, c_=bpy.data.collections["OR_Set"])
bed.parent = bed_root
BED_TOP = 0.62
blanket = box("Blanket", (0.82, 1.35, 0.06), (0, -0.25, BED_TOP + 0.12), mat("Blanket", (0.82, 0.86, 0.9), 0.85), bpy.data.collections["OR_Set"], bevel=0.03)
blanket.parent = bed_root
BED_PATH = [(766, V(1.75, 5.6, 0)), (784, V(1.75, 4.9, 0)), (860, V(1.75, 3.0, 0)), (940, V(1.72, 2.25, 0)), (990, V(1.72, 2.15, 0))]
bp_ = pchip([(f, p) for f, p in BED_PATH]) if False else None
bpx = pchip([(f, p.x) for f, p in BED_PATH]); bpy_ = pchip([(f, p.y) for f, p in BED_PATH])
for f in list(range(766, 991, 4)) + [990]:
    bed_root.location = V(bpx(f), bpy_(f), 0); bed_root.keyframe_insert("location", frame=f)
bed_root.location = V(1.75, 5.6, 0); bed_root.keyframe_insert("location", frame=1)
bed_root.location = V(1.72, 2.15, 0); bed_root.keyframe_insert("location", frame=1710)
for f in list(range(792, 1000, 8)) + [1000, 1060]:
    lie(PT, f, V(bpx(min(f, 990)), bpy_(min(f, 990)) + 0.1, BED_TOP + 0.10), 0, arms=4)
lie(PT, 1066, pt_pos, 90); lie(PT, 1710, pt_pos, 90)
PT.bake()
stepped(PT.o, {600, 790, 1060})
pt_body = bpy.data.objects["Patient.body"]
gi = pt_body.vertex_groups
hv = pt_body.vertex_groups.new(name="head_only")
idx = {g.index: g.name for g in pt_body.vertex_groups}
for v in pt_body.data.vertices:
    w_ = sum(g.weight for g in v.groups if idx.get(g.group, "") in ("head", "neck01", "neck02", "neck03", "jaw") or idx.get(g.group, "").startswith(("oris", "levator", "orbicularis", "oculi", "risorius", "temporalis", "special", "eye")))
    if w_ > 0.5:
        hv.add([v.index], 1.0, 'REPLACE')
mk = pt_body.modifiers.new("head_only", 'MASK'); mk.vertex_group = "head_only"
bpy.context.view_layer.objects.active = pt_body
while pt_body.modifiers.find("head_only") > 0:
    bpy.ops.object.modifier_move_up(modifier="head_only")
for f, on in ((0, True), (601, False), (1062, True)):
    mk.show_render = on; mk.show_viewport = on; pt_body.keyframe_insert('modifiers["head_only"].show_render', frame=f)
for fc in fcurves(pt_body):
    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
vis(part("Patient", "female_casualsuit02") + part("Patient", "shoes01"), [(601, 791)])
vis(part("Patient", "male_casualsuit06"), [(792, 1061)])
def mod_vis(body_name, mod, ranges):
    ob = bpy.data.objects[body_name]; m = ob.modifiers[mod]
    m.show_render = False; ob.keyframe_insert('modifiers["%s"].show_render' % mod, frame=0)
    for f0, f1 in ranges:
        m.show_render = True; ob.keyframe_insert('modifiers["%s"].show_render' % mod, frame=f0)
        m.show_render = False; ob.keyframe_insert('modifiers["%s"].show_render' % mod, frame=f1 + 1)
    for fc in fcurves(ob):
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
mod_vis("Patient.body", "Delete.male_casualsuit06", [(792, 1061)])
mod_vis("Patient.body", "Delete.female_casualsuit02", [(601, 791)])
mod_vis("Surgeon1.body", "Delete.male_casualsuit01", [(0, 1100)])
mod_vis("Surgeon1.body", "Delete.male_elegantsuit01", [(1101, 1710)])
vis([blanket], [(0, 1061)])
vis([bpy.data.objects["Drape"], bpy.data.objects["AbdomenSkin"], bpy.data.objects["Incision"]], [(0, 600), (1000, 1710)])
vis([o for o in bpy.data.objects if o.name.startswith("Suture_")], [(0, 600)])

# ================================================================== NURSE
nu_or = V(0.85, 0.62, NU.ROOT.z - 0.02); YN = -10
STN = NU.stance(nu_or, YN); FN = {s: (STN[s], YN) for s in "LR"}
lamp1 = bpy.data.objects["SurgLamp_1"]
def lamp_handle(f):
    ev(f); M = lamp1.matrix_world; h = M @ V(0, 0, -0.13)
    return h + V(0, 0, -0.03), V(0, 0, 1), V(0, -1, 0)
NU.P(1, nu_or, YN, spine=(6, 0, 0), head=(10, 0, -4), feet=FN, hands={"L": ("body", (V(0.14, -0.30, 1.0), V(-0.6, -0.4, -0.6), V(-0.2, 1, 0))), "R": ("body", (V(-0.14, -0.30, 1.0), V(0.6, -0.4, -0.6), V(0.2, 1, 0)))})
NU.P(30, nu_or, YN - 8, spine=(6, 0, -6), head=(-26, 0, 0), feet=FN, hands={"L": ("world", (V(0.55, 0.28, skin_z(0.55, 0.25) + 0.03), V(-0.2, -1, -0.5), V(0, 0, -1))), "R": ("world", (V(0.3, 0.28, skin_z(0.3, 0.25) + 0.03), V(-0.2, -1, -0.5), V(0, 0, -1)))}, curl={"L": (28, 20), "R": (28, 20)})
NU.P(90, nu_or, YN - 8, spine=(8, 0, -4), head=(-20, -6, 0), feet=FN, hands={"L": ("world", (V(0.55, 0.28, skin_z(0.55, 0.25) + 0.03), V(-0.2, -1, -0.5), V(0, 0, -1))), "R": ("world", (V(0.3, 0.28, skin_z(0.3, 0.25) + 0.03), V(-0.2, -1, -0.5), V(0, 0, -1)))}, curl={"L": (28, 20), "R": (28, 20)})
NU.P(130, nu_or, YN, spine=(10, 0, 0), head=(18, 0, 0), feet=FN, hands={"L": ("world", (V(0.55, 0.28, skin_z(0.55, 0.25) + 0.03), V(-0.2, -1, -0.5), V(0, 0, -1))), "R": ("world", (V(0.3, 0.28, skin_z(0.3, 0.25) + 0.03), V(-0.2, -1, -0.5), V(0, 0, -1)))})
for f in (250, 380, 470):
    NU.P(f, nu_or + V(0, 0, -0.01 * (f % 2)), YN, spine=(12, 0, 2), head=(20, 6 * math.sin(f), 0), feet=FN, hands={"L": ("world", (V(0.55, 0.28, skin_z(0.55, 0.25) + 0.03), V(-0.2, -1, -0.5), V(0, 0, -1))), "R": ("world", (V(0.3, 0.28, skin_z(0.3, 0.25) + 0.03), V(-0.2, -1, -0.5), V(0, 0, -1)))})
NU.P(530, nu_or, YN - 30, spine=(2, 0, -10), head=(0, -30, 0), feet=FN, hands={"L": ("rest", dict(fwd=20, out=6, bend=0.3)), "R": ("rest", dict(fwd=20, out=6, bend=0.3))})
NU.P(600, nu_or, YN - 30, spine=(2, 0, -10), head=(4, -34, 0), feet=FN, hands={"L": ("rest", dict(fwd=20, out=6, bend=0.3)), "R": ("rest", dict(fwd=20, out=6, bend=0.3))})
# pushes the bed: walks behind its head end, hands on the head-board rail
HB = V(0.0, 1.12, 0.95)       # head-board grab bar, bed local
def bed_grip(s, f):
    p = V(bpx(min(f, 990)), bpy_(min(f, 990)), 0) + HB + V(0.22 if s == "R" else -0.22, 0, 0)
    return p, V(0, -1, -0.3), V(0, 0, -1)
nu_path = lambda f: V(bpx(min(f, 990)), bpy_(min(f, 990)) + 1.6, 0)
NU.H.walk(nu_path, lambda f: 0.0, 766, 990, stride=0.72, lean=12, crouch=0.05)
for f in range(780, 991, 10):
    pass
NU.bake()
# hands for the push (after the walk keyed the body)
for f in list(range(766, 991, 6)) + [990, 1100]:
    for s in "LR":
        W, d, n = bed_grip(s, f)
        NU.R.key_world("IK_hand." + s, f, NU.hand_matrix(s, W, d, n))
stepped(NU.o, {600})
vis([NU.o.name + "." + x for x in ("body",)] + [c for c in NU.o.children], [(0, 1300)])

# ================================================================== ANAESTHETIST (background life at the head end)
an_pos = V(-1.22, 0.42, AN.ROOT.z - 0.02); YA = 150
STA = AN.stance(an_pos, YA); FA = {s: (STA[s], YA) for s in "LR"}
monA = bpy.data.objects["Monitor_B"]
def screen_touch(f):
    ev(f); M = monA.matrix_world; return M @ V(0.12, -0.03, -0.05), (M.to_3x3() @ V(0, 1, 0.3)).normalized(), (M.to_3x3() @ V(0, 1, 0)).normalized()
for i, f in enumerate(range(1, 1711, 45)):
    look_mon = (i % 3 != 2)
    hands = {"L": ("body", (V(0.16, -0.30, 1.0), V(-0.5, -0.5, -0.6), V(-0.2, 1, 0))), "R": ("fn", screen_touch) if i % 4 == 1 else ("body", (V(-0.16, -0.30, 1.0), V(0.5, -0.5, -0.6), V(0.2, 1, 0)))}
    AN.P(f, an_pos + V(0.01 * math.sin(i), 0, -0.005 * (i % 2)), YA + (0 if look_mon else -35), spine=(8, 0, 4 if look_mon else -10),
         head=((-6, 22, 0) if look_mon else (14, -20, 0)), feet=FA, hands=hands, curl={"R": (25, 18) if i % 4 == 1 else (30, 22)}, face={"brow": 0.2 * (i % 2)})
AN.bake()
vis(["Anaesth"] + [c for c in AN.o.children] + [CAPS["Anaesth"], MASKS["Anaesth"]] + list(MASKS["Anaesth"].children), [(0, 1240)])

# ================================================================== SURGEON 2
s2_start = V(-1.75, 2.45, S2.ROOT.z - 0.02); s2_end = V(-0.3, 0.68, S2.ROOT.z - 0.02); Y2 = 0
ST2a = S2.stance(s2_start, 160); F2a = {s: (ST2a[s], 160) for s in "LR"}
ST2 = S2.stance(s2_end, Y2, 1.1); F2 = {s: (ST2[s], Y2) for s in "LR"}
def glove_pull(f, s="R"):
    return {"L": ("body", (V(-0.05, -0.36, 1.18), V(-1, -0.2, 0.1), V(0, 0, -1))), "R": ("body", (V(-0.16, -0.34, 1.22), V(-0.2, -0.3, 1), V(1, 0, 0)))}
S2.P(850, s2_start, 160, spine=(14, 0, 0), head=(20, 0, 0), feet=F2a, hands={"L": ("body", (V(0.06, -0.40, 1.02), V(-0.6, -0.5, -0.3), V(0, 0, -1))), "R": ("body", (V(-0.06, -0.40, 1.04), V(0.6, -0.5, -0.3), V(0, 0, 1)))})
S2.P(870, s2_start, 160, spine=(10, 0, 0), head=(10, 0, 0), feet=F2a, hands={"L": ("body", (V(0.10, -0.36, 1.12), V(-0.6, -0.5, 0.3), V(0, 0, 1))), "R": ("body", (V(-0.10, -0.36, 1.12), V(0.6, -0.5, 0.3), V(0, 0, 1)))})
S2.bake()
walk2 = lambda f: s2_start.lerp(s2_end, smooth((f - 878) / 112.0))
yaw2 = lambda f: 160 + (Y2 - 160) * smooth((f - 878) / 40.0)
S2.H.walk(walk2, yaw2, 878, 990, stride=0.7, lean=8)
S2.poses = []
S2.P(1000, s2_end, Y2, spine=(4, 0, 0), head=(6, 0, 0), feet=F2, hands=glove_pull(1000))
S2.P(1016, s2_end, Y2, spine=(4, 0, 0), head=(4, 0, 0), feet=F2, hands={"L": ("body", (V(-0.02, -0.40, 1.16), V(-1, -0.2, 0.1), V(0, 0, -1))), "R": ("body", (V(-0.16, -0.34, 1.22), V(-0.2, -0.3, 1), V(1, 0, 0)))}, curl={"L": (55, 40)})
S2.P(1030, s2_end + V(0, -0.02, 0), Y2, spine=(12, 0, 0), head=(18, 0, 0), feet=F2, hands={"L": ("rest", dict(fwd=30, out=6, bend=0.4)), "R": ("rest", dict(fwd=30, out=6, bend=0.4))})
HW = lambda dx: ("world", (V(WIN.x + dx, WIN.y + 0.12, skin_w + 0.02), V(0, -1, -0.6), V(0, 0, -1)))
S2.P(1050, s2_end + V(0, -0.04, -0.02), Y2, spine=(26, 0, 0), head=(26, 0, 0), feet=F2, hands={"L": HW(0.07), "R": HW(-0.07)})
S2.P(1170, s2_end + V(0, -0.04, -0.02), Y2, spine=(28, 0, 0), head=(28, 0, 0), feet=F2, hands={"L": HW(0.07), "R": HW(-0.07)})
S2.P(1192, s2_end + V(0, -0.02, -0.01), Y2, spine=(18, 0, 0), head=(14, 0, 0), feet=F2, hands={"L": HW(0.08), "R": HW(-0.08)}, face={"wide": 0.6, "brow": -0.6})
S2.P(1212, s2_end + V(0, 0.02, 0.0), Y2, spine=(4, 0, 0), head=(-4, 0, 0), feet=F2, hands={"L": ("rest", dict(fwd=35, out=10, bend=0.5)), "R": ("rest", dict(fwd=35, out=10, bend=0.5))}, face={"wide": 1.0, "brow": -1.0, "jaw": 5})
S2.P(1260, s2_end + V(0, 0.03, 0.0), Y2, spine=(2, 0, 0), head=(-6, 0, 0), feet=F2, hands={"L": ("rest", dict(fwd=30, out=10, bend=0.5)), "R": ("rest", dict(fwd=30, out=10, bend=0.5))}, face={"wide": 1.0, "brow": -1.0, "jaw": 6})
for f, p in S2.poses:
    S2.key_body(f, p)
for f, p in S2.poses:
    S2.key_feet(f, p)
for f, p in S2.poses:
    S2.key_hands(f, p)
# hands during the walk: swing loosely
for f in range(880, 1000, 10):
    ev(f); M = S2.R.delta("spine01"); R3 = M.to_3x3()
    for s in "LR":
        W, d, n = S2.arm_rest(s, fwd=12 * math.sin((f - 890) / 14.0 + (0 if s == "L" else math.pi)), out=6)
        S2.R.key_world("IK_hand." + s, f, S2.hand_matrix(s, M @ W, R3 @ d, R3 @ n))
vis(["Surgeon2"] + [c for c in S2.o.children] + [CAPS["Surgeon2"], MASKS["Surgeon2"]] + list(MASKS["Surgeon2"].children), [(878, 1300)])

# ================================================================== PANEL (seated)
def seated(act, y, notes=False):
    pos = V(-10.62, y, DAIS_H + 0.5 + 0.06); YW = 90
    feet = {s: (V(-10.17, y + (0.12 if s == "L" else -0.12)), YW) for s in "LR"}
    return pos, YW, feet
def desk(act, s, y, dx=0.0, dy=0.0, up=0.0):
    sx = 1 if s == "L" else -1
    return ("world", (V(-10.18 + dx, y + 0.22 * sx + dy, DAIS_H + 0.835 + up), V(1, -0.2 * sx, -0.05), V(0, 0, -1)))
gavel = [o for o in bpy.data.objects if o.name.startswith("Gavel_src")]
gav_mats = {o.data.materials[0].name: o for o in gavel}
stand = gav_mats.get("stand"); head_parts = [gav_mats.get(k) for k in ("body", "side1", "side2", "stick") if gav_mats.get(k)]
# rescale the gavel to real size: stick 0.26 m
for o in gavel:
    o.data.transform(Matrix.Scale(0.36 / 1.292, 4))
gav = bpy.data.objects.new("Gavel", None); bpy.data.collections["Hearing_Set"].objects.link(gav)
for o in head_parts:
    o.parent = gav; o.location = (0, 0, 0)
stand.location = V(-10.02, 0.12, DAIS_H + 0.785)
GAV_REST = V(-10.12, 0.42, DAIS_H + 0.80)
def gkey(f, loc, rz, rx=0.0):
    gav.location = loc; gav.rotation_euler = (rx, 0, rz); gav.keyframe_insert("location", frame=f); gav.keyframe_insert("rotation_euler", frame=f)
gkey(1, GAV_REST, R_(10)); gkey(1480, GAV_REST, R_(10))
GH_LOC = lambda f: gav.matrix_world @ V(0.0, -0.15, 0.03)
def gavel_hand(f):
    """hammer grip: palm over the handle, fingers wrap across it, thumb on the far side"""
    ev(f); M = gav.matrix_world; R3 = M.to_3x3()
    grip = M @ V(0.0, -0.20, 0.0)
    return grip + R3 @ V(-0.045, 0.0, 0.035), (R3 @ V(1, 0, -0.35)).normalized(), (R3 @ V(0, 0, -1)).normalized()
gkey(1500, GAV_REST + V(0.02, -0.05, 0.12), R_(5), R_(-20))
gkey(1525, V(-10.14, 0.30, DAIS_H + 1.04), R_(0), R_(-55))
gkey(1538, V(-10.03, 0.28, DAIS_H + 0.86), R_(0), R_(8))
gkey(1546, V(-10.04, 0.29, DAIS_H + 0.92), R_(0), R_(-10))
gkey(1570, V(-10.08, 0.32, DAIS_H + 0.90), R_(0), R_(-5))
gkey(1710, V(-10.08, 0.32, DAIS_H + 0.90), R_(0), R_(-5))
pos, YW, feet = seated(PA, 0.0)
for f in (1200, 1300, 1420):
    PA.P(f, pos + V(0.02 * (f % 3), 0, 0), YW, spine=(14, 0, 0), head=(6, 0, 0), feet=feet, hands={"L": desk(PA, "L", 0.0), "R": desk(PA, "R", 0.0)}, face={"brow": 0.4})
PA.P(1480, pos, YW, spine=(14, 0, -6), head=(10, -10, 0), feet=feet, hands={"L": desk(PA, "L", 0.0), "R": ("fn", gavel_hand)}, curl={"R": (78, 45)}, face={"brow": 0.6})
for f in (1500, 1525, 1538, 1546, 1570, 1710):
    PA.P(f, pos + V(0.03 if f == 1538 else 0, 0, 0), YW, spine=(10 if f != 1538 else 20, 0, -8), head=(4 if f != 1538 else 12, -6, 0), feet=feet,
         hands={"L": desk(PA, "L", 0.0), "R": ("fn", gavel_hand)}, curl={"R": (78, 45)}, face={"brow": 0.8})
PA.bake()
pos, YW, feet = seated(PBn, -1.2)
stamp = bpy.data.objects["Stamp"]
CERT = V(-10.05, -1.0, DAIS_H + 0.79)
bpy.data.objects["Certificate"].location = CERT + V(0, 0, 0)
for o in bpy.data.objects:
    if o.name.startswith(("CertLine", "CertSeal", "CertBorder", "StampMark")) and o.parent is None:
        o.location = o.location + (CERT - V(-9.8, -0.75, DAIS_H + 0.79))
def skey(f, loc, rx=0.0):
    stamp.location = loc; stamp.rotation_euler = (rx, 0, R_(35)); stamp.keyframe_insert("location", frame=f); stamp.keyframe_insert("rotation_euler", frame=f)
ST_REST = V(-10.2, -1.38, DAIS_H + 0.785)
skey(1, ST_REST); skey(1560, ST_REST); skey(1578, ST_REST + V(0.06, 0.1, 0.16), R_(-10)); skey(1592, CERT + V(0, 0, 0.004 + 0.02), R_(0))
skey(1596, CERT + V(0, 0, 0.004)); skey(1606, CERT + V(0, 0, 0.004)); skey(1625, CERT + V(-0.1, -0.15, 0.10)); skey(1710, CERT + V(-0.12, -0.2, 0.08))
def stamp_hand(f):
    """palm on the knob, fingers wrapped over it"""
    ev(f); M = stamp.matrix_world; R3 = M.to_3x3()
    return M @ V(-0.05, 0.0, 0.15), (R3 @ V(1, 0, -0.45)).normalized(), (R3 @ V(0, 0, -1)).normalized()
key_vis([bpy.data.objects["StampMark"]] + list(bpy.data.objects["StampMark"].children), [(1596, 1710)])
for f in (1200, 1300, 1400, 1500):
    PBn.P(f, pos, YW, spine=(16, 0, 4), head=(18 if f % 200 else 4, 8, 0), feet=feet, hands={"L": desk(PBn, "L", -1.2, dy=0.2), "R": desk(PBn, "R", -1.2, dx=0.05 * (f % 300 == 0))}, face={"brow": 0.3})
for f in (1560, 1578, 1592, 1596, 1606, 1625):
    PBn.P(f, pos + V(0.04 if f in (1592, 1596) else 0, 0, 0), YW, spine=(18 if f in (1592, 1596) else 10, 0, 4), head=(16, 8, 0), feet=feet,
          hands={"L": desk(PBn, "L", -1.2, dy=0.2), "R": ("fn", stamp_hand)}, curl={"R": (72, 42)}, face={"brow": 0.6})
PBn.P(1710, pos, YW, spine=(10, 0, 2), head=(6, 12, 0), feet=feet, hands={"L": desk(PBn, "L", -1.2, dy=0.2), "R": desk(PBn, "R", -1.2)})
PBn.bake()
pos, YW, feet = seated(PC, 1.2)
for i, f in enumerate(range(1200, 1711, 30)):
    wr = 0.02 * math.sin(i * 1.9)
    PC.P(f, pos, YW, spine=(18 if i % 4 < 2 else 8, 0, -4), head=(24 if i % 4 < 2 else 2, -10 if i % 4 >= 2 else 0, 0), feet=feet,
         hands={"L": desk(PC, "L", 1.2), "R": desk(PC, "R", 1.2, dx=0.05 + wr, dy=0.02 * math.cos(i * 1.3))}, curl={"R": (55, 40)})
PC.bake()
vis([a.o.name for a in (PA, PBn, PC)] + [c for a in (PA, PBn, PC) for c in a.o.children], [(1200, 1710)])

# ================================================================== STUDIO: liver, letters, pen, sparks, smoke, glove hands
liver = bpy.data.objects["Liver"]
dg = bpy.context.evaluated_depsgraph_get()
LW = liver.matrix_world.copy(); LWi = LW.inverted()
def project(u, v):
    """point on the liver's front (-Y) surface at world x=u, z=v offsets from the liver centre"""
    c_ = liver.location + V(0, 0, 0.084)
    o_ = LWi @ V(c_.x + u, c_.y - 0.4, c_.z + v); d_ = (LWi.to_3x3() @ V(0, 1, 0)).normalized()
    hit, loc, nrm, _ = liver.ray_cast(o_, d_)
    return (loc, nrm) if hit else (None, None)
def letter_pts(ch, cx, cz, h=0.05):
    w = h * 0.62
    pts = []
    if ch == "S":
        for i in range(61):
            t = i / 60.0
            a = math.pi * (0.25 + 1.5 * t * 2) if t < 0.5 else None
            if t < 0.5:
                a = math.radians(30) + t * 2 * math.radians(255)
                pts.append((cx + w / 2 * math.cos(a), cz + h / 4 + h / 4 * math.sin(a)))
            else:
                a = math.radians(105) - (t - 0.5) * 2 * math.radians(255)
                pts.append((cx + w / 2 * math.cos(a), cz - h / 4 + h / 4 * math.sin(a)))
    else:   # B: stem up, upper bowl down to the waist, lower bowl down to the foot
        x0 = cx - w / 2; r = h / 4
        for i in range(15): pts.append((x0, cz - h / 2 + h * i / 14))
        for i in range(5): pts.append((x0 + w * 0.42 * i / 4, cz + h / 2))
        for i in range(1, 19):
            a = math.pi / 2 - math.pi * i / 18; pts.append((x0 + w * 0.42 + r * 0.95 * math.cos(a), cz + r + r * math.sin(a)))
        for i in range(1, 5): pts.append((x0 + w * 0.42 - w * 0.36 * i / 4, cz))
        for i in range(1, 5): pts.append((x0 + w * 0.06 + w * 0.44 * i / 4, cz - 0.0004))
        for i in range(1, 19):
            a = math.pi / 2 - math.pi * i / 18; pts.append((x0 + w * 0.50 + r * 1.1 * math.cos(a), cz - r + r * math.sin(a)))
        for i in range(1, 6): pts.append((x0 + w * 0.52 - w * 0.52 * i / 5, cz - h / 2))
    return pts
M_SEAR = mat("Seared", (0.03, 0.015, 0.012), 0.75, emit=(1.0, 0.35, 0.08), estr=0.0)
M_HOT = emis("HotTrail", (1.0, 0.62, 0.25), 30.0)
LETTERS = {}
for ch, cx in (("S", -0.035), ("B", 0.03)):
    pts3 = []
    for u, v in letter_pts(ch, cx, 0.01):
        loc, nrm = project(u, v)
        if loc is not None:
            pts3.append(loc + nrm * 0.0008)
    print("LETTER", ch, len(pts3))
    for kind, m, bev in (("Sear", M_SEAR, 0.0030), ("Hot", M_HOT, 0.0036)):
        cu = bpy.data.curves.new("Brand_%s_%s" % (ch, kind), 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = bev; cu.bevel_resolution = 2
        sp = cu.splines.new('POLY'); sp.points.add(len(pts3) - 1)
        for p, co in zip(sp.points, pts3):
            p.co = (*co, 1)
        cu.use_fill_caps = True
        ob = bpy.data.objects.new(cu.name, cu); bpy.data.collections["Studio_Set"].objects.link(ob); cu.materials.append(m)
        ob.parent = liver
        LETTERS[ch, kind] = (ob, pts3)
WRITE = {"S": (160, 214), "B": (222, 286)}
for ch, (f0, f1) in WRITE.items():
    sear, _ = LETTERS[ch, "Sear"]; hot, _ = LETTERS[ch, "Hot"]
    for ob in (sear, hot):
        ob.data.bevel_factor_end = 0.0; ob.data.keyframe_insert("bevel_factor_end", frame=f0)
        ob.data.bevel_factor_end = 1.0; ob.data.keyframe_insert("bevel_factor_end", frame=f1)
    hot.data.bevel_factor_start = 0.0; hot.data.keyframe_insert("bevel_factor_start", frame=f0 + 8)
    hot.data.bevel_factor_start = 0.86; hot.data.keyframe_insert("bevel_factor_start", frame=f1)
    hot.data.bevel_factor_start = 1.0; hot.data.keyframe_insert("bevel_factor_start", frame=f1 + 14)
    for fc in fcurves(sear.data) + fcurves(hot.data):
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
# seared letters cool from glowing to a dark brand with an ember edge
sp_node = M_SEAR.node_tree.nodes["Principled BSDF"].inputs['Emission Strength']
for f, v in ((150, 0.0), (165, 1.2), (300, 0.25), (600, 0.08), (1100, 0.08), (1160, 0.35), (1710, 0.3)):
    sp_node.default_value = v; sp_node.keyframe_insert("default_value", frame=f)
# the studio pen follows the strokes (tip on the surface), the glove hand follows the pen
pen = bpy.data.objects["ArgonPen_Studio"]
AXS = V(0.25, -0.25, 0.95)
def path_at(ch, t):
    _, pts = LETTERS[ch, "Sear"]
    seg = [0.0]
    for a, b in zip(pts, pts[1:]): seg.append(seg[-1] + (b - a).length)
    L = seg[-1] * t
    for i in range(len(pts) - 1):
        if seg[i + 1] >= L:
            u = (L - seg[i]) / max(1e-6, seg[i + 1] - seg[i]); return LW @ pts[i].lerp(pts[i + 1], u)
    return LW @ pts[-1]
TIP = {}
key_tool(pen, 1, path_at("S", 0) + V(0.03, -0.12, 0.14), AXS)
key_tool(pen, 140, path_at("S", 0) + V(0.02, -0.08, 0.08), AXS)
key_tool(pen, 156, path_at("S", 0) + V(0, -0.004, 0.003), AXS)
for ch, (f0, f1) in WRITE.items():
    for f in range(f0, f1 + 1, 2):
        t = (f - f0) / (f1 - f0); p = path_at(ch, t); TIP[f] = p
        key_tool(pen, f, p + V(0, -0.0015, 0.0), AXS + V(0.05 * math.sin(f / 9), 0, 0))
key_tool(pen, 218, path_at("B", 0) + V(0, -0.02, 0.02), AXS)
key_tool(pen, 300, path_at("B", 1) + V(0.04, -0.14, 0.12), AXS)
key_tool(pen, 1710, path_at("B", 1) + V(0.04, -0.14, 0.12), AXS)
# tip glow light + tip sphere
tl = bpy.data.lights.new("TipGlow", 'POINT'); tl.color = (0.7, 0.9, 1.0); tl.shadow_soft_size = 0.002
tlo = bpy.data.objects.new("TipGlow", tl); bpy.data.collections["Studio_Set"].objects.link(tlo); tlo.parent = pen; tlo.location = (0, 0, -0.03)
for f, e in ((150, 0.0), (158, 6.0), (214, 6.0), (218, 0.5), (222, 6.0), (286, 6.0), (292, 0.0)):
    tl.energy = e; tl.keyframe_insert("energy", frame=f)
tip = bpy.data.objects.new("TipFlare", bpy.data.meshes.new("TipFlare")); bpy.data.collections["Studio_Set"].objects.link(tip)
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.0022); bm.to_mesh(tip.data); bm.free()
tip.data.materials.append(emis("TipFlare", (0.75, 0.92, 1.0), 60.0)); tip.parent = pen; tip.location = (0, 0, -0.03)
key_vis([tip], [(157, 214), (222, 286)])
# sparks: pooled streaks, ballistic, script keyed (no simulation)
M_SPARK = emis("Spark", (1.0, 0.75, 0.35), 45.0)
POOL = []
for i in range(40):
    s_ = cyl("Spark_%02d" % i, 0.0005, 0.007, (0, 0, 0), M_SPARK, bpy.data.collections["Studio_Set"], verts=6)
    s_.hide_render = True; s_.keyframe_insert("hide_render", frame=0); POOL.append([s_, 0])
for f in sorted(TIP):
    if f % 4: continue
    for _ in range(3):
        slot = min(POOL, key=lambda x: x[1])
        if slot[1] > f: continue
        s_ = slot[0]; life = random.randint(7, 13)
        p0 = TIP[f] + V(0, -0.002, 0)
        vel = V(random.uniform(-0.6, 0.6), random.uniform(-0.9, -0.2), random.uniform(0.1, 0.9)) * 0.9
        for k in range(0, life + 1, 2):
            t = k / 60.0
            s_.location = p0 + vel * t + V(0, 0, -4.9 * t * t)
            v_ = vel + V(0, 0, -9.8 * t)
            s_.rotation_euler = V(0, 0, 1).rotation_difference(v_.normalized()).to_euler()
            s_.keyframe_insert("location", frame=f + k); s_.keyframe_insert("rotation_euler", frame=f + k)
        s_.hide_render = False; s_.keyframe_insert("hide_render", frame=f)
        s_.hide_render = True; s_.keyframe_insert("hide_render", frame=f + life)
        slot[1] = f + life + 1
for s_, _ in POOL:
    set_constant(s_)
# smoke puffs: soft volume, rising and fading
for i, f0 in enumerate((168, 190, 212, 236, 258, 280)):
    me = bpy.data.meshes.new("Smoke"); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=0.012); bm.to_mesh(me); bm.free()
    sm = bpy.data.objects.new("Smoke_%d" % i, me); bpy.data.collections["Studio_Set"].objects.link(sm)
    m = bpy.data.materials.new("Smoke_%d" % i); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o_ = nt.nodes.new('ShaderNodeOutputMaterial'); pv = nt.nodes.new('ShaderNodeVolumePrincipled'); nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 90.0; mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    nt.links.new(nz.outputs['Fac'], mul.inputs[0]); nt.links.new(mul.outputs[0], pv.inputs['Density']); nt.links.new(pv.outputs[0], o_.inputs['Volume'])
    pv.inputs['Color'].default_value = (0.85, 0.87, 0.9, 1)
    me.materials.append(m)
    p0 = TIP.get(f0, TIP[max(k for k in TIP if k <= f0)])
    for k, (sc_, den) in enumerate(((0.5, 0.0), (1.0, 60.0), (2.2, 30.0), (3.5, 0.0))):
        f = f0 + k * 14
        sm.location = p0 + V(0.004 * k, -0.01 * k, 0.018 * k * k); sm.scale = (sc_, sc_, sc_ * 1.4)
        sm.keyframe_insert("location", frame=f); sm.keyframe_insert("scale", frame=f)
        mul.inputs[1].default_value = den; mul.inputs[1].keyframe_insert("default_value", frame=f)
    key_vis([sm], [(f0, f0 + 44)])
# glove hands: right hand holds the pen; left steadies the liver; then (beat 6) both lift the liver into the light
gh_pos = V(0.0, 0.36, (LIVER_Z := liver.location.z + 0.084) + 0.33 - GH.SH["L"].z + GH.ROOT.z)
GH.P(1, gh_pos, 0, spine=(30, 0, 0), feet="body", hands={"R": ("fn", tool_hand(pen, 0.08)), "L": ("world", (liver.location + V(0.10, 0.06, 0.185), V(-0.3, -0.6, -0.8), V(0, 0.3, -1)))}, curl={"R": (55, 40), "L": (25, 18)})
for f in range(140, 301, 12):
    GH.P(f, gh_pos + V(0.01 * math.sin(f / 20), 0, 0), 0, spine=(30, 0, 0), feet="body", hands={"R": ("fn", tool_hand(pen, 0.08)), "L": ("world", (liver.location + V(0.10, 0.06, 0.185), V(-0.3, -0.6, -0.8), V(0, 0.3, -1)))}, curl={"R": (55, 40), "L": (25, 18)})
# beat 6: liver keys + cupping hands
L0 = liver.location.copy(); R0 = liver.rotation_euler.copy()
def lkey(f, dz, rz, rx=0.0):
    liver.location = L0 + V(0, -0.02 * dz / 0.14, dz); liver.rotation_euler = (R0.x + rx, R0.y, R0.z + rz)
    liver.keyframe_insert("location", frame=f); liver.keyframe_insert("rotation_euler", frame=f)
lkey(1, 0, 0); lkey(1075, 0, 0); lkey(1100, 0.05, R_(-8), R_(4)); lkey(1135, 0.14, R_(-22), R_(10)); lkey(1180, 0.17, R_(-26), R_(12)); lkey(1710, 0.17, R_(-26), R_(12))
def cup(s):
    sx = 1 if s == "L" else -1
    def fn(f):
        ev(f); M = liver.matrix_world
        W = M @ V(-sx * (0.145 if s == "L" else 0.10), 0.03, -0.02)      # fingers under the lobe edge (the right lobe is narrower)
        return W, (M.to_3x3() @ V(sx * 0.6, -0.3, 0.4)).normalized(), (M.to_3x3() @ V(sx * 0.4, 0, 1)).normalized()
    return fn
gh6 = V(0.0, 0.32, LIVER_Z - 0.15 - GH.SH["L"].z + GH.ROOT.z + 0.35)
GH.P(1040, gh6 + V(0, 0.15, -0.2), 0, spine=(10, 0, 0), feet="body", hands={"L": ("rest", dict(fwd=40, out=10, bend=0.4)), "R": ("rest", dict(fwd=40, out=10, bend=0.4))})
for f in (1070, 1100, 1135, 1180, 1300):
    GH.P(f, gh6 + V(0, 0, 0.17 * smooth((f - 1075) / 105.0)), 0, spine=(18, 0, 0), feet="body", hands={"L": ("fn", cup("L")), "R": ("fn", cup("R"))}, curl={"L": (35, 25), "R": (35, 25)})
GH.bake()
stepped(GH.o, {300, 1040})
vis(["GloveHands", "GloveHands.body"], [(100, 310), (1040, 1200)])
# light shaft for the reveal
beam = bpy.data.lights.new("RevealSpot", 'SPOT'); beam.spot_size = R_(26); beam.spot_blend = 0.5; beam.color = (1.0, 0.95, 0.85)
bo = bpy.data.objects.new("RevealSpot", beam); bpy.data.collections["Studio_Set"].objects.link(bo)
bo.location = liver.location + V(-0.2, -0.6, 1.2); bo.rotation_euler = (liver.location + V(0, 0, 0.25) - bo.location).to_track_quat('-Z', 'Y').to_euler()
for f, e in ((1, 0), (1090, 0), (1130, 260), (1200, 260)):
    beam.energy = e; beam.keyframe_insert("energy", frame=f)

# ================================================================== HOME x-ray liver (pulses blue -> red)
xl = bpy.data.objects.new("XRayLiver_Home", liver.data.copy()); bpy.data.collections["Home_Set"].objects.link(xl)
mx_ = bpy.data.objects["GhostLiver_0"].data.materials[0].copy(); xl.data.materials.clear(); xl.data.materials.append(mx_)
em_n = [n for n in mx_.node_tree.nodes if n.type == 'EMISSION'][0]; gn = mx_.node_tree.nodes["XRayGain"]
ev(700)
xl.scale = (0.62, 0.62, 0.62)
xl.rotation_euler = (0, 0, 0)
PT.child_of_bone(xl, "spine03") if False else None
xl.location = V(-0.07, -0.19, PT.R.BN["spine02"].head_local.z - 0.01); xl.rotation_euler = (0, 0, R_(180)); xl.scale = (0.85, 0.85, 0.85)
xl.data.transform(Matrix.Translation(V(0, 0, -0.084)))
PT.child_of_bone(xl, "spine03")
for f, col, g in ((640, (0.35, 0.85, 1.0), 0.0), (660, (0.35, 0.85, 1.0), 5.0), (690, (1.0, 0.25, 0.12), 8.0), (705, (1.0, 0.25, 0.12), 3.0),
                  (720, (1.0, 0.2, 0.1), 9.0), (740, (1.0, 0.2, 0.1), 3.5), (760, (1.0, 0.18, 0.08), 9.0), (790, (1.0, 0.18, 0.08), 4.0)):
    em_n.inputs['Color'].default_value = (*col, 1); em_n.inputs['Color'].keyframe_insert("default_value", frame=f)
    gn.inputs[1].default_value = g; gn.inputs[1].keyframe_insert("default_value", frame=f)
key_vis([xl], [(645, 791)])
# ghost livers in the hearing room light up one after another
for i, g in enumerate(o for o in bpy.data.objects if o.name.startswith("GhostLiver_")):
    gm = g.data.materials[0]; gg = gm.node_tree.nodes["XRayGain"]
    for f, v in ((1, 2.5), (1262 + i * 14, 2.5), (1270 + i * 14, 14.0), (1300 + i * 14, 6.0), (1710, 6.0)):
        gg.inputs[1].default_value = v; gg.inputs[1].keyframe_insert("default_value", frame=f)
    # small glowing brand mark on each ghost
    for ch, cx in (("S", -0.035), ("B", 0.03)):
        ob, pts = LETTERS[ch, "Sear"]
        cp = bpy.data.objects.new("GhostBrand_%d_%s" % (i, ch), ob.data.copy()); bpy.data.collections["Hearing_Set"].objects.link(cp)
        cp.data.materials.clear(); cp.data.materials.append(emis("GhostBrand", (1.0, 0.45, 0.15), 6.0))
        cp.data.animation_data_clear(); cp.data.bevel_factor_end = 1.0
        cp.parent = g; cp.matrix_parent_inverse = Matrix.Identity(4)
        cp.location = (0, 0, 0); cp.rotation_euler = (0, 0, 0); cp.scale = (1, 1, 1)
        # letters were built in liver space; ghost shares that local space
# doors swing open as the bed arrives, swing back
for side, sg in (("L", -1), ("R", 1)):
    h = bpy.data.objects["DoorHinge_" + side]
    for f, a in ((1, 0), (770, 0), (790, 82), (905, 82), (940, -8), (955, 3), (970, 0), (1710, 0)):
        h.rotation_euler = (0, 0, R_(a * sg)); h.keyframe_insert("rotation_euler", frame=f)
# calendar pages flip up and over (one day each, fast)
for k, pg in enumerate(o for o in bpy.data.objects if o.name.startswith("CalPage_")):
    if k == 7:
        break
    f0 = 572 + k * 7
    pg.rotation_euler = (0, 0, 0); pg.keyframe_insert("rotation_euler", frame=f0)
    pg.rotation_euler = (R_(-200), 0, 0); pg.keyframe_insert("rotation_euler", frame=f0 + 9)
    key_vis([c for c in pg.children], [(0, f0 + 6)])
# curtains breathe
for cu in [o for o in bpy.data.objects if o.name.startswith("HOME_Curtain")]:
    for f in range(600, 800, 30):
        cu.rotation_euler = (R_(3 * math.sin(f / 23.0)), 0, 0); cu.keyframe_insert("rotation_euler", frame=f)
key_vis([pen] + [c for c in pen.children], [(100, 300)])
# anaesthesia mask + tube over the patient's mouth and nose while she lies on the table
ev(100); jb = PT.R.PB["jaw"]; mouth = PT.o.matrix_world @ (jb.head.lerp(jb.tail, 0.8))
ev(100); hb = PT.R.PB["head"]; face_up = (PT.o.matrix_world.to_3x3() @ (hb.matrix.to_3x3() @ V(0, 0, -1))).normalized()
am = bpy.data.objects.new("AnaesthesiaMask", None); bpy.data.collections["OR_Set"].objects.link(am)
am.location = mouth + V(0, 0, 0.035); am.rotation_euler = V(0, 0, 1).rotation_difference(V(0, 0, 1)).to_euler()
cone = cyl("AnaesMaskCone", 0.045, 0.05, (0, 0, 0), mat("AnaesMask", (0.75, 0.9, 0.85), 0.1, trans=0.6), bpy.data.collections["OR_Set"], verts=24)
cone.data.transform(Matrix.Scale(1.0, 4)); cone.parent = am
for v in cone.data.vertices:
    if v.co.z > 0: v.co.x *= 0.4; v.co.y *= 0.4
cyl("AnaesMaskRim", 0.047, 0.01, (0, 0, -0.025), mat("AnaesRim", (0.2, 0.25, 0.3), 0.5), bpy.data.collections["OR_Set"], verts=24).parent = am
cu = bpy.data.curves.new("AnaesTube", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.011
sp = cu.splines.new('BEZIER'); sp.bezier_points.add(2)
for bp, co in zip(sp.bezier_points, (am.location + V(0, 0, 0.03), am.location + V(-0.3, 0.3, 0.35), V(-1.4, 0.75, 1.05))):
    bp.co = co; bp.handle_left_type = bp.handle_right_type = 'AUTO'
tb = bpy.data.objects.new("AnaesTube", cu); bpy.data.collections["OR_Set"].objects.link(tb); cu.materials.append(mat("Tube", (0.55, 0.7, 0.8), 0.3, trans=0.4))
ev(100); nk = PT.o.matrix_world @ PT.R.PB["neck01"].head
towel = cyl("NeckTowel", 0.085, 0.2, nk + V(0.02, 0, 0.0), M_DRAPE_T := mat("NeckTowel", (0.05, 0.20, 0.38), 0.85), bpy.data.collections["OR_Set"], verts=24, rot=(0, R_(90), 0))
key_vis([am, tb, towel] + list(am.children), [(0, 600), (1062, 1710)])

# ================================================================== BURN 'SB' INTO THE LIVER SURFACE (replaces the tube letters)
# Each stroke point is projected onto the mesh, converted to UV, and rasterised into a 1K mask:
#   R = frame the pen tip reaches that spot (normalised), G = line coverage (soft edge).
# The shader compares R with a keyed progress value: seared char behind the tip, a hot orange edge only at the tip.
import numpy as np
from mathutils import geometry as mgeo
me_l = liver.data
uvl = me_l.uv_layers.active_render or me_l.uv_layers.active
def surf_uv(p_local):
    """closest surface point -> (uv, polygon); p_local is already on the surface"""
    ok, loc, nrm, fi = liver.closest_point_on_mesh(p_local)
    poly = me_l.polygons[fi]; vs = [me_l.vertices[i].co for i in poly.vertices]; uvs = [uvl.data[li].uv for li in poly.loop_indices]
    best = None
    for k in range(1, len(vs) - 1):
        tri = (vs[0], vs[k], vs[k + 1]); tuv = (uvs[0].to_3d(), uvs[k].to_3d(), uvs[k + 1].to_3d())
        u = mgeo.barycentric_transform(loc, *tri, *tuv)
        cp = mgeo.closest_point_on_tri(loc, *tri); d = (cp - loc).length
        if best is None or d < best[0]: best = (d, u.to_2d())
    return best[1]
RES = 1024
ARR = np.ones((RES, RES), np.float32) * 2.0; COV = np.zeros((RES, RES), np.float32)
LINE_W = 0.0022            # metres: half-width of the burn line
B0, B1 = 150.0, 300.0      # progress 0..1 spans frames 150..300
strokes = []
for ch in ("S", "B"):
    _, pts = LETTERS[ch, "Sear"]
    f0, f1 = WRITE[ch]
    seg = [0.0]
    for a_, b_ in zip(pts, pts[1:]): seg.append(seg[-1] + (b_ - a_).length)
    for i, p_ in enumerate(pts):
        fr = f0 + (f1 - f0) * seg[i] / seg[-1]
        strokes.append((ch, p_, surf_uv(p_), (fr - B0) / (B1 - B0)))
for (c0, p0, u0, t0), (c1, p1, u1, t1) in zip(strokes, strokes[1:]):
    if c0 != c1: continue
    wl = max(1e-6, (p1 - p0).length); ul = (u1 - u0).length
    if ul > 0.05: continue                      # UV seam jump: skip that segment
    scale = ul / wl if ul > 1e-7 else 0.004 / 0.001
    rad = LINE_W * scale * RES                  # pixels
    rad = max(1.5, min(rad, 30))
    x0, y0 = u0.x * RES, u0.y * RES; x1, y1 = u1.x * RES, u1.y * RES
    xa, xb = int(min(x0, x1) - rad - 2), int(max(x0, x1) + rad + 2); ya, yb = int(min(y0, y1) - rad - 2), int(max(y0, y1) + rad + 2)
    xa, ya = max(0, xa), max(0, ya); xb, yb = min(RES - 1, xb), min(RES - 1, yb)
    if xb <= xa or yb <= ya: continue
    X, Y = np.meshgrid(np.arange(xa, xb + 1), np.arange(ya, yb + 1))
    dx, dy = x1 - x0, y1 - y0; L2 = dx * dx + dy * dy + 1e-9
    tt = np.clip(((X - x0) * dx + (Y - y0) * dy) / L2, 0, 1)
    d = np.hypot(X - (x0 + tt * dx), Y - (y0 + tt * dy))
    cov = np.clip(1.0 - d / rad, 0, 1) ** 0.6
    arr = t0 + (t1 - t0) * tt
    sub_c = COV[ya:yb + 1, xa:xb + 1]; sub_a = ARR[ya:yb + 1, xa:xb + 1]
    m_ = cov > 0
    sub_a[m_] = np.minimum(sub_a[m_], arr[m_]); sub_c[:] = np.maximum(sub_c, cov)
print("BURN mask pixels", int((COV > 0).sum()))
img_b = bpy.data.images.new("BrandBurnMask", RES, RES, alpha=False, float_buffer=True)
px = np.zeros((RES, RES, 4), np.float32); px[..., 0] = ARR; px[..., 1] = COV; px[..., 3] = 1.0
img_b.pixels.foreach_set(px.ravel()); img_b.update()
MASK_PATH = os.path.join(os.path.dirname(OUT), "brand_burn_mask.png")
img_b.file_format = 'PNG'; img_b.save(filepath=MASK_PATH)
bpy.data.images.remove(img_b)
img_b = bpy.data.images.load(MASK_PATH); img_b.name = "BrandBurnMask"; img_b.colorspace_settings.name = 'Non-Color'; img_b.pack()
def burn_nodes(nt, uvname):
    n, l = nt.nodes, nt.links
    uvn = n.new('ShaderNodeUVMap'); uvn.uv_map = uvname
    tx = n.new('ShaderNodeTexImage'); tx.image = img_b; tx.interpolation = 'Linear'; tx.extension = 'CLIP'
    l.new(uvn.outputs[0], tx.inputs['Vector'])
    sp_ = n.new('ShaderNodeSeparateColor'); l.new(tx.outputs['Color'], sp_.inputs[0])
    return sp_
def mth(nt, op, a, b=None, clamp=False):
    m = nt.nodes.new('ShaderNodeMath'); m.operation = op; m.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None: continue
        if isinstance(v, (int, float)): m.inputs[i].default_value = v
        else: nt.links.new(v, m.inputs[i])
    return m.outputs[0]
lmat = liver.data.materials[0]; nt = lmat.node_tree; n, l = nt.nodes, nt.links
pr = n["Principled BSDF"]
sp_ = burn_nodes(nt, uvl.name)
R, G = sp_.outputs[0], sp_.outputs[1]
prog = n.new('ShaderNodeValue'); prog.name = "BurnProgress"
for f, v in ((1, -1.0), (B0, 0.0), (B1, 1.0), (1710, 1.0)):
    prog.outputs[0].default_value = v; prog.outputs[0].keyframe_insert("default_value", frame=f)
for fc in fcurves(nt):
    if "BurnProgress" in fc.data_path:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
P = prog.outputs[0]
behind = mth(nt, 'SUBTRACT', P, R)                       # >0 where the tip has passed
burnt = mth(nt, 'GREATER_THAN', behind, 0.0)
sear = mth(nt, 'MULTIPLY', burnt, G)                     # 0..1 char amount
cool = mth(nt, 'SUBTRACT', 1.0, mth(nt, 'DIVIDE', behind, 0.035), clamp=True)   # 1 at the tip, 0 after ~5 frames of travel
hot = mth(nt, 'MULTIPLY', sear, cool)
# base colour: wet liver -> char brown-black, rougher
mixc = n.new('ShaderNodeMix'); mixc.data_type = 'RGBA'; mixc.blend_type = 'MIX'
src = pr.inputs['Base Color'].links[0].from_socket if pr.inputs['Base Color'].links else None
if src: l.new(src, mixc.inputs['A'])
else: mixc.inputs['A'].default_value = pr.inputs['Base Color'].default_value
mixc.inputs['B'].default_value = (0.012, 0.006, 0.004, 1)
l.new(mth(nt, 'MULTIPLY', sear, 1.0), mixc.inputs['Factor']); l.new(mixc.outputs['Result'], pr.inputs['Base Color'])
l.new(mth(nt, 'ADD', 0.32, mth(nt, 'MULTIPLY', sear, 0.6), clamp=True), pr.inputs['Roughness'])
l.new(mth(nt, 'SUBTRACT', 0.7, mth(nt, 'MULTIPLY', sear, 1.0), clamp=True), pr.inputs['Coat Weight'])
# glow only at the tip (plus a faint ember in the char)
em_s = mth(nt, 'ADD', mth(nt, 'MULTIPLY', hot, 60.0), mth(nt, 'MULTIPLY', mth(nt, 'MULTIPLY', sear, sear), 0.04))
pr.inputs['Emission Color'].default_value = (1.0, 0.42, 0.1, 1); l.new(em_s, pr.inputs['Emission Strength'])
# slight raised char
bump = n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.6; bump.inputs['Distance'].default_value = 0.0015
l.new(sear, bump.inputs['Height'])
if pr.inputs['Normal'].links:
    l.new(pr.inputs['Normal'].links[0].from_socket, bump.inputs['Normal'])
l.new(bump.outputs['Normal'], pr.inputs['Normal'])
# retire the tube letters (kept hidden as camera/pen references)
for ch in ("S", "B"):
    for kind in ("Sear", "Hot"):
        ob = LETTERS[ch, kind][0]; ob.hide_render = True
        if ob.data.animation_data: ob.data.animation_data_clear()
# ghost livers: the same mask glows in their x-ray shader; remove their tube copies
for o in [o for o in bpy.data.objects if o.name.startswith("GhostBrand_")]:
    bpy.data.objects.remove(o, do_unlink=True)
for g in [o for o in bpy.data.objects if o.name.startswith("GhostLiver_")]:
    gm = g.data.materials[0]; gt = gm.node_tree
    sp2 = burn_nodes(gt, uvl.name)
    out = [x for x in gt.nodes if x.type == 'OUTPUT_MATERIAL'][0]; prev = out.inputs['Surface'].links[0].from_socket
    e2 = gt.nodes.new('ShaderNodeEmission'); e2.inputs['Color'].default_value = (1.0, 0.45, 0.15, 1)
    gt.links.new(mth(gt, 'MULTIPLY', sp2.outputs[1], 9.0), e2.inputs['Strength'])
    ad = gt.nodes.new('ShaderNodeAddShader'); gt.links.new(prev, ad.inputs[0]); gt.links.new(e2.outputs[0], ad.inputs[1]); gt.links.new(ad.outputs[0], out.inputs['Surface'])

# tissue membrane in the studio: the camera passes through it on every dive / rise (the transit wipe)
mb = bpy.data.meshes.new("StudioMembrane"); import bmesh as _bm; bmm = _bm.new(); _bm.ops.create_grid(bmm, x_segments=60, y_segments=60, size=0.8)
for v in bmm.verts: v.co.z = 0.01 * noise.noise(v.co * 9.0) if 'noise' in globals() else 0.0
bmm.to_mesh(mb); bmm.free()
for p_ in mb.polygons: p_.use_smooth = True
memb = bpy.data.objects.new("StudioMembrane", mb); bpy.data.collections["Studio_Set"].objects.link(memb)
memb.location = (0.0, -0.1, liver.location.z + 0.084 + 0.45)
mm = mat("Membrane", (0.72, 0.42, 0.36), 0.35, sss=0.3, coat=0.4, emit=(0.75, 0.38, 0.32), estr=0.6); mb.materials.append(mm)
mnt = mm.node_tree; nz = mnt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 60.0; nz.inputs['Detail'].default_value = 8.0
bp = mnt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35; mnt.links.new(nz.outputs['Fac'], bp.inputs['Height']); mnt.links.new(bp.outputs['Normal'], mnt.nodes["Principled BSDF"].inputs['Normal'])
src_img = [nd.image for nd in liver.data.materials[0].node_tree.nodes if nd.type == 'TEX_IMAGE' and nd.image and nd.image.name.startswith("Image_0")]
if src_img:
    tci = mnt.nodes.new('ShaderNodeTexCoord'); mpi = mnt.nodes.new('ShaderNodeMapping'); mpi.inputs['Scale'].default_value = (2.5, 2.5, 2.5)
    ti = mnt.nodes.new('ShaderNodeTexImage'); ti.image = src_img[0]
    mnt.links.new(tci.outputs['Generated'], mpi.inputs['Vector']); mnt.links.new(mpi.outputs['Vector'], ti.inputs['Vector'])
    prm = mnt.nodes["Principled BSDF"]
    mnt.links.new(ti.outputs['Color'], prm.inputs['Base Color']); mnt.links.new(ti.outputs['Color'], prm.inputs['Emission Color'])
key_vis([memb], [(126, 152), (262, 292), (1046, 1074), (1166, 1192)])
print("ANIM_DONE")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
