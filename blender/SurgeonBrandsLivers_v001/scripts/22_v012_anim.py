"""v012 animation pass (client rejection, Nov 21: items 7-13, 16-17, 19-20, 23-25, 27-32). VO timing (v011 frames).
blender -b in.blend --python 22_v012_anim.py -- <out.blend>
Shots (hard cuts): S1 1-135 OR wide, S2 136-275 branding macro, S3 276-429 stitching, S4 430-570 mask down,
S5 571-640 calendar walk, S6 641-775 home, S7 776-915 bed through the doors, S8 916-1060 new doctor walks in,
S9 1061-1175 liver lifted, S10 1176-1240 doctor's eyes, S11 1241-1445 hearing, S12 1446-1575 gavel, S13 1576-1644 stamp."""
import sys, os, math, json
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion, Euler
HERE = os.path.dirname(os.path.abspath(__file__)); PIPE = os.path.join(HERE, "..", "..", "pipeline")
sys.path.insert(0, HERE)
import v12lib as VL
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
V = lambda *a: Vector(a); R_ = math.radians
HP = {}; exec(open(os.path.join(PIPE, "hand_poses.py")).read(), HP)
AL = {}; exec(open(os.path.join(PIPE, "anim_lib.py")).read(), AL); AL["ground_z"] = lambda x, y: 0.0
SITE = json.load(open(os.path.join(os.path.dirname(OUT), "or_site.json")))
CX, CY, SKZ = SITE["CX"], SITE["CY"], SITE["SKZ"]
OB = bpy.data.objects
def human(name): return AL["Human"](AL["Rig"](OB[name]))
def ev(f): sc.frame_set(int(f))
def W(r, b, tail=False):
    pb = r.pose.bones[b]; return r.matrix_world @ (pb.tail if tail else pb.head)
def clear_bones(r, bones, a, b):
    VL.clear_keys(r, tuple('pose.bones["%s"]' % n for n in bones), a, b)
SPINE = ["root", "spine05", "spine04", "spine03", "spine02", "spine01", "neck01", "neck02", "neck03", "head"]
LIMB = ["IK_foot.L", "IK_foot.R", "IK_hand.L", "IK_hand.R", "Pole_knee.L", "Pole_knee.R", "Pole_elbow.L", "Pole_elbow.R"]
def body_bones(): return SPINE + LIMB
def smooth(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

def face(r, f, smile=0.0, wide=0.3, brow=0.0, jaw=0.0, close=0.0):
    PB = r.pose.bones
    for s in "LR":
        sx = 1 if s == "L" else -1
        for n in ("risorius02.", "risorius03."):
            pb = PB[n + s]; pb.location = V(0.010 * smile * sx, 0, 0.008 * smile); pb.keyframe_insert("location", frame=f, group=n + s)
        pb = PB["orbicularis03." + s]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion((1, 0, 0), R_(25 * wide - 32 * close))
        pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
        pb = PB["orbicularis04." + s]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion((1, 0, 0), R_(-25 * wide + 8 * close))
        pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
        for n in ("oculi01.", "oculi02."):
            pb = PB[n + s]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion((1, 0, 0), R_(20 * brow))
            pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
    pb = PB["jaw"]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion((1, 0, 0), R_(jaw)); pb.keyframe_insert("rotation_quaternion", frame=f, group="jaw")
def blink(r, f, base):
    face(r, f - 3, **base); b2 = dict(base); b2["close"] = 1.0; b2["wide"] = 0.0
    face(r, f, **b2); face(r, f + 4, **base)
def eyes(r, f, yaw=0.0, pitch=0.0):
    for s in "LR":
        pb = r.pose.bones["eye." + s]; pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Quaternion((0, 0, 1), R_(yaw)) @ Quaternion((1, 0, 0), R_(pitch)); pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)

def restrict_vis(ob, spans):
    """keep ob's own visibility, but only inside spans"""
    fc = [f for f in VL.fcurves(ob) if f.data_path == "hide_render"]
    own = sorted((int(k.co.x), bool(k.co.y)) for k in fc[0].keyframe_points) if fc and len(fc[0].keyframe_points) else [(0, ob.hide_render)]
    def own_hidden(f):
        h = own[0][1]
        for x, v in own:
            if x <= f: h = v
        return h
    edges = sorted({0} | {x for x, _ in own} | {a for a, b in spans} | {b + 1 for a, b in spans})
    VL.clear_keys(ob, ("hide_render",))
    for e in edges:
        inside = any(a <= e <= b for a, b in spans)
        ob.hide_render = own_hidden(e) or not inside; ob.keyframe_insert("hide_render", frame=e)
    VL.constant(ob, ("hide_render",))
def rig_objs(name):
    r = OB[name]; return [r] + [c for c in r.children_recursive]

def swing_arms(name, f0, f1, yaw_fn, phase_fn, amp=0.15, step=2, out_k=0.09):
    """relaxed walking arms: elbows bent, opposite to the legs, hands near the thighs"""
    r = OB[name]; Hm = human(name)
    clear_bones(r, ["IK_hand.L", "IK_hand.R", "Pole_elbow.L", "Pole_elbow.R"], f0, f1)
    for f in list(range(f0, f1 + 1, step)) + [f1]:
        ev(f); y = R_(yaw_fn(f)); fwd = V(math.sin(y), -math.cos(y), 0); rt = V(-math.cos(y), -math.sin(y), 0)
        ph = 2 * math.pi * phase_fn(f)
        for s, sg in (("L", 1), ("R", -1)):
            out = -rt if s == "L" else rt
            sh = W(r, "upperarm01." + s)
            Wp = sh + V(0, 0, -0.47) + fwd * (0.07 + amp * math.sin(ph) * sg) + out * out_k
            d = (V(0, 0, -1) + fwd * 0.25).normalized(); n = -out
            pole = sh + V(0, 0, -0.30) - fwd * 0.4 + out * 0.30
            Hm.key_hand(s, f, Wp, d, n, pole)
        HP["apply_pose"](r, "L", "relaxed", f); HP["apply_pose"](r, "R", "relaxed", f)

def hold_pose(r, bones, f):
    """key the evaluated pose of `bones` at f (so nothing drifts into the next shot's motion)"""
    ev(f)
    for n in bones:
        pb = r.pose.bones[n]
        pb.keyframe_insert("location", frame=f, group=n); pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
def walk(name, path, f0, f1, stride=0.68, lean=5.0, out_k=0.09, amp=0.15):
    r = OB[name]; Hm = human(name)
    hold_pose(r, body_bones(), f0 - 1)
    clear_bones(r, body_bones(), f0, f1)
    def yaw(f):
        a, b = path(max(f0, f - 2)), path(min(f1, f + 2)); d = b - a
        return math.degrees(math.atan2(d.x, -d.y)) if d.length > 1e-4 else 0.0
    Hm.walk(path, yaw, f0, f1, stride=stride, lean=lean)
    frames = list(range(f0, f1 + 1)); dist = [0.0]
    for a_, b_ in zip(frames, frames[1:]): dist.append(dist[-1] + (path(b_) - path(a_)).to_2d().length)
    phase = lambda f: dist[min(len(dist) - 1, max(0, f - f0))] / stride
    swing_arms(name, f0, f1, yaw, phase, amp=amp, out_k=out_k)
    return yaw

# =================================================================== S3: stitching the closed incision (276-429)
INC_SPAN = [(352, 600)]
s1 = OB["Surgeon1"]
def body_top(x, y):
    return SKZ + 0.0   # flat enough across 20 cm of the upper abdomen at this scale; refined below by ray cast
pb_ = OB["Patient.body"]
ev(350); dg = bpy.context.evaluated_depsgraph_get()
from mathutils.bvhtree import BVHTree
for mm in pb_.modifiers:
    if mm.name.startswith("Delete."): mm.show_viewport = False
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
ev_ = pb_.evaluated_get(dg); me_ = ev_.to_mesh()
BODY = BVHTree.FromPolygons([pb_.matrix_world @ v.co for v in me_.vertices], [tuple(p.vertices) for p in me_.polygons]); ev_.to_mesh_clear()
for mm in pb_.modifiers:
    if mm.name.startswith("Delete."): mm.show_viewport = True
def skin(x, y):
    h = BODY.ray_cast(V(x, y, 2.0), V(0, 0, -1), 2.0); return h[0].z if h[0] is not None else SKZ
# incision line along the cavity's long axis (across the body), sutures crossing it
M_INC = bpy.data.materials.new("IncisionLine"); M_INC.use_nodes = True
bb = M_INC.node_tree.nodes["Principled BSDF"]; bb.inputs["Base Color"].default_value = (0.35, 0.05, 0.05, 1); bb.inputs["Roughness"].default_value = 0.3
M_SUT = bpy.data.materials.new("SutureThread"); M_SUT.use_nodes = True
bb = M_SUT.node_tree.nodes["Principled BSDF"]; bb.inputs["Base Color"].default_value = (0.05, 0.08, 0.35, 1); bb.inputs["Roughness"].default_value = 0.35
Y0, Y1 = CY - 0.095, CY + 0.095
cu = bpy.data.curves.new("IncisionNew", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0014
sp = cu.splines.new('POLY'); N = 24; sp.points.add(N - 1)
for i in range(N):
    y = Y0 + (Y1 - Y0) * i / (N - 1); sp.points[i].co = (CX + 0.002 * math.sin(i * 1.3), y, skin(CX, y) + 0.0006, 1)
inc = OB.new("IncisionNew", cu); bpy.data.collections["OR_Set"].objects.link(inc); cu.materials.append(M_INC)
VL.key_hide(inc, INC_SPAN)
NST = 7; STY = [Y0 + 0.012 + (Y1 - Y0 - 0.024) * k / (NST - 1) for k in range(NST)]
ST_F = [354, 358] + [370 + 11 * k for k in range(NST - 2)]       # v014: the wound closes 280-360, then the stitches go in
for k, y in enumerate(STY):
    cu = bpy.data.curves.new("Stitch", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0009
    sp = cu.splines.new('POLY'); pts = [V(CX - 0.009, y, 0), V(CX - 0.004, y + 0.001, 0.0025), V(CX + 0.004, y + 0.001, 0.0025), V(CX + 0.009, y, 0)]
    sp.points.add(len(pts) - 1)
    for p_, c_ in zip(sp.points, pts): p_.co = (c_.x, c_.y, skin(c_.x, c_.y) + c_.z, 1)
    ob = OB.new("Stitch", cu); bpy.data.collections["OR_Set"].objects.link(ob); cu.materials.append(M_SUT)
    VL.key_hide(ob, [(max(352, ST_F[k]), 600)])
# needle-driver tip path: for each new stitch, in at one lip, under, out of the other, pull the thread up
nd = OB["NeedleDriver"]
def nd_tip(f):
    for k in range(2, NST):
        a, b = ST_F[k] - 11, ST_F[k]
        if a <= f <= b:
            u = (f - a) / max(1, b - a); y = STY[k]
            P = [V(CX - 0.02, y - 0.004, 0.025), V(CX - 0.009, y, 0.002), V(CX + 0.009, y, 0.002), V(CX + 0.02, y + 0.004, 0.03), V(CX + 0.01, STY[min(k + 1, NST - 1)] - 0.004, 0.045)]
            t = u * (len(P) - 1); i = min(int(t), len(P) - 2); w = smooth(t - i)
            p = P[i].lerp(P[i + 1], w); return V(p.x, p.y, skin(p.x, p.y) + p.z)
    if f < ST_F[2] - 11:
        p = V(CX - 0.02, STY[2] - 0.004, 0.035); return V(p.x, p.y, skin(p.x, p.y) + p.z)
    p = V(CX + 0.01, STY[-1] + 0.01, 0.05 + 0.002 * (f - ST_F[-1])); return V(p.x, p.y, skin(p.x, p.y) + p.z)
for f in range(276, 430):
    HP["apply_pose"](s1, "R", "pinch", f) if f in (276, 429) else None
gap = VL.hold_path("Surgeon1", "R", nd, 276, 429, nd_tip, 280, head_clear=0.22)
print("ND hold gap cm", round(gap * 100, 2))
restrict_vis(nd, [(276, 429)])
for c in nd.children_recursive: restrict_vis(c, [(276, 429)])
# left hand: flat on the drape beside the wound, steadying (no hand through anything)
clear_bones(s1, ["IK_hand.L", "Pole_elbow.L"], 276, 429)
for f in (276, 330, 380, 429):
    ev(f); p = V(CX - 0.11, CY - 0.10, 0); p.z = skin(p.x, p.y) + 0.02
    HP["place_hand"](s1, "L", f, p, V(0, 0, -1), V(0.15, 1, 0).normalized(), skin=0.012)
    HP["apply_pose"](s1, "L", "relaxed", f)

# =================================================================== S4: mask down + smirk; ear loops stay on the ears
mk = OB["Surgeon1_Mask"]
ev(1)
for lo in [c for c in mk.children if c.type == 'CURVE']:
    pw = lo.matrix_world @ lo.data.splines[0].bezier_points[1].co
    an = OB.new(lo.name + "_Ear", None); bpy.data.collections["People"].objects.link(an)
    an.location = pw; an.parent = s1; an.parent_type = 'BONE'; an.parent_bone = "head"
    ev(1); an.matrix_world = Matrix.Translation(pw)
    hk = lo.modifiers.new("Ear", 'HOOK'); hk.object = an
    hk.vertex_indices_set([3, 4, 5])
    ev(1); hk.matrix_inverse = an.matrix_world.inverted() @ lo.matrix_world
for f, kw in ((430, dict(wide=0.3)), (470, dict(wide=0.35, brow=0.1)), (500, dict(smile=0.7, wide=0.2, brow=0.35)),
              (540, dict(smile=0.9, wide=0.15, brow=0.2)), (570, dict(smile=0.8, wide=0.2, brow=0.25))):
    face(s1, f, **kw)
blink(s1, 455, dict(wide=0.33, brow=0.05)); blink(s1, 528, dict(smile=0.85, wide=0.18, brow=0.25))
# v013: his right arm lifts from his side to the mask edge (no popping), follows it down, then both hands peel the gloves
clear_bones(s1, ["IK_hand.L", "IK_hand.R", "Pole_elbow.L", "Pole_elbow.R"], 430, 570)
ev(462); mvs = [(mk.matrix_world @ v.co, v.index) for v in mk.data.vertices]
ymed = sorted(p.y for p, i in mvs)[len(mvs) // 2]
edge_i = min([(p.z, i) for p, i in mvs if p.y > ymed])[1]; edge_l = mk.data.vertices[edge_i].co.copy()
def s1_fwd(f):
    ev(f); M = s1.matrix_world @ s1.pose.bones["spine02"].matrix; return (M.to_3x3() @ V(0, 0, 1)).normalized()
def put_pole(r, s, f, pole):
    pbp = r.pose.bones["Pole_elbow." + s]; pbp.location = r.data.bones["Pole_elbow." + s].matrix_local.to_3x3().inverted() @ (pole - r.data.bones["Pole_elbow." + s].head_local)
    pbp.keyframe_insert("location", frame=f, group=pbp.name)
for f in range(430, 571, 2):
    ev(f); sh = {s: W(s1, "upperarm01." + s) for s in "LR"}
    hip = {s: W(s1, "upperleg01." + s) for s in "LR"}
    fw = (W(s1, "spine02") - W(s1, "spine04")).cross(sh["L"] - sh["R"]).normalized()
    if fw.dot(V(0, 1, 0)) < 0: fw = -fw
    fw.z = 0; fw.normalize()
    side = {s: hip[s] + fw * 0.14 + (sh[s] - sh["L" if s == "R" else "R"]).normalized() * 0.11 + V(0, 0, 0.04) for s in "LR"}
    waist = (hip["L"] + hip["R"]) / 2 + fw * 0.33 + V(0, 0, 0.12)
    edge = mk.matrix_world @ edge_l
    def drape_pt(sv):
        q = W(s1, "upperarm01." + sv) + fw * 0.30; q.z = 2.0
        h_ = OB["DrapeFit"].ray_cast(OB["DrapeFit"].matrix_world.inverted() @ q, OB["DrapeFit"].matrix_world.inverted().to_3x3() @ V(0, 0, -1))
        z_ = (OB["DrapeFit"].matrix_world @ h_[1]).z if h_[0] else 1.08
        return V(q.x, q.y, z_ + 0.004)
    drapeR, drapeL = drape_pt("R"), drape_pt("L")
    belly = (hip["L"] + hip["R"]) / 2 + fw * 0.42 + V(0, 0, 0.12) + (sh["R"] - sh["L"]).normalized() * 0.05
    # right hand
    if f <= 446: P = side["R"].lerp(edge + fw * 0.04 - V(0, 0, 0.12), smooth((f - 430) / 16.0))
    elif f <= 462: P = (edge + fw * 0.04 - V(0, 0, 0.12)).lerp(edge + fw * 0.07 - V(0, 0, 0.012), smooth((f - 446) / 16.0))
    elif f <= 505: P = edge + fw * 0.07 - V(0, 0, 0.012)
    elif f <= 525: P = (edge + fw * 0.10).lerp(belly + V(0, 0, 0), smooth((f - 505) / 20.0))
    else: P = belly + V(0.01 * math.sin(f / 9.0), 0, 0.012 * math.sin(f / 6.0))
    d = (V(0, 0, 1) + fw * 0.3).normalized() if 446 < f <= 505 else (fw + V(0, 0, -0.3)).normalized()
    n = (-fw).normalized() if 446 < f <= 505 else V(0, 0, -1)
    HP["place_hand"](s1, "R", f, P, n, d, skin=0.02)
    up_ = smooth((f - 436) / 14.0) * (1 - smooth((f - 505) / 16.0))
    put_pole(s1, "R", f, sh["R"] + V(0, 0, -0.35 + 0.25 * up_) + fw * (0.05 + 0.45 * up_) + (sh["R"] - sh["L"]).normalized() * 0.5)
    # left hand: at his side, then meets the right glove cuff (peeling it) from 524
    kL = smooth((f - 512) / 16.0)
    PL = side["L"].lerp(belly + (sh["L"] - sh["R"]).normalized() * 0.09 + V(0, 0, -0.01), kL)   # left hand meets the right glove cuff
    HP["place_hand"](s1, "L", f, PL, (-(sh["L"] - sh["R"]).normalized()), (fw + V(0, 0, -0.5 * (1 - kL))).normalized(), skin=0.02)
    put_pole(s1, "L", f, sh["L"] + V(0, 0, -0.40) + fw * 0.05 + (sh["L"] - sh["R"]).normalized() * 0.5)
    HP["apply_pose"](s1, "R", "pinch" if 450 <= f <= 505 else "relaxed", f); HP["apply_pose"](s1, "L", "relaxed", f)
# head acting after the mask is down: a glance at the patient, a look up, a slight nod
R1 = AL["Rig"](s1)
clear_bones(s1, ["head", "neck02"], 500, 570)
for f, yaw, pit in ((500, 0, 0), (516, 16, 8), (532, 14, 6), (548, -6, -4), (560, -4, 4), (570, -6, -2)):
    R1.key_rot("head", f, [("X", pit * 0.6), ("Z", yaw * 0.6)]); R1.key_rot("neck02", f, [("X", pit * 0.4), ("Z", yaw * 0.4)])
eyes(s1, 500, 0, 0); eyes(s1, 512, 8, 0); eyes(s1, 535, 8, 0); eyes(s1, 548, -4, 0); eyes(s1, 570, -4, 0)

# =================================================================== S5: a week later - he walks past the calendar (571-640)
s1w = lambda f: V(2.85, 0.6, 0).lerp(V(2.45, -1.35, 0), smooth((f - 571) / 69.0) * 0.85 + 0.15 * (f - 571) / 69.0)
walk("Surgeon1", s1w, 571, 640, stride=0.66)
face(s1, 571, smile=0.4, wide=0.3); face(s1, 640, smile=0.5, wide=0.3); blink(s1, 600, dict(smile=0.45, wide=0.3))
for o in rig_objs("Surgeon1"):
    if o.type in ('MESH', 'CURVE', 'ARMATURE'): restrict_vis(o, [(0, 640), (1176, 1700)])
for o in (OB["Surgeon1_Cap"], OB["Surgeon1_Mask"]) + tuple(OB["Surgeon1_Mask"].children): restrict_vis(o, [(0, 640)])
# v014: the calendar does not flip (sheets flapped/popped); it shows the later week
for k in range(7):
    for nm_ in ("CalPage_%d" % k, "CalPaper_%d" % k):
        if OB.get(nm_): VL.key_hide(OB[nm_], [])
        for c_ in (OB[nm_].children_recursive if OB.get(nm_) else []): VL.key_hide(c_, [])


# =================================================================== S6: the woman walks in, the pain hits (641-775)
pt = OB["Patient"]; HW = human("Patient")
P0, P1 = V(6.45, 1.05, 0), V(5.85, -0.30, 0)
wpath = lambda f: P0.lerp(P1, smooth((f - 641) / 62.0) * 0.6 + 0.4 * (f - 641) / 62.0)
yaw_w = walk("Patient", wpath, 641, 703, stride=0.62, lean=4, out_k=0.075, amp=0.13)
clear_bones(pt, body_bones(), 704, 775)
y0 = yaw_w(703); yr = R_(y0); fwd = V(math.sin(yr), -math.cos(yr), 0); rt = V(-math.cos(yr), -math.sin(yr), 0)
for s in "LR":
    xy = HW.foot_xy(s, V(P1.x, P1.y, 0), y0)
    for f in (704, 775): HW.key_foot(s, f, xy, y0)
rz = HW.root_head.z
for f, dz, fl, hd in ((704, 0.0, 6, 0), (716, -0.02, 14, -4), (730, -0.05, 28, -18), (750, -0.07, 34, -32), (775, -0.07, 35, -36)):
    HW.key_root(f, V(P1.x, P1.y, rz + dz) - fwd * 0.02 * (fl / 40), yaw=y0, flex=fl * 0.35)
    HW.key_spine(f, flex=fl, twist=-4 * (fl / 40), side=4 * (fl / 40), head=(hd, 6 * fl / 40))
# hands: right hand presses her right side over the liver (on the shirt), left hand on her left thigh
for f in list(range(704, 776, 3)) + [775]:
    ev(f)
    sp2 = W(pt, "spine02"); r_side = sp2 + rt * 0.075 + fwd * 0.10 + V(0, 0, -0.02)
    hit = None
    so = OB["Patient.female_casualsuit01"]
    k = smooth((f - 704) / 22.0)
    if f <= 726:
        sh = W(pt, "upperarm01.R"); r_side = (sh + V(0, 0, -0.5) + fwd * 0.05 + rt * 0.05).lerp(r_side, k)
    nrm_in = (-(fwd * 0.85 + rt * 0.5)).normalized()
    dgw = bpy.context.evaluated_depsgraph_get(); ew = so.evaluated_get(dgw); Mi_ = so.matrix_world.inverted()
    okh, loch, nh, ih = ew.ray_cast(Mi_ @ (r_side - nrm_in * 0.25), Mi_.to_3x3() @ nrm_in, distance=0.5)
    if okh and f > 712 and ((so.matrix_world @ loch) - r_side).length < 0.08: r_side = r_side.lerp(so.matrix_world @ loch, min(1.0, k * 1.2))
    HP["place_hand"](pt, "R", f, r_side, nrm_in, (-rt * 0.8 + V(0, 0, -0.6)).normalized(), skin=0.016)
    HP["apply_pose"](pt, "R", "cup_hold", f)
    thL = W(pt, "upperleg02.L").lerp(W(pt, "lowerleg01.L"), 0.55) + fwd * 0.07 - rt * 0.07
    shL = W(pt, "upperarm01.L"); l_pt = (shL + V(0, 0, -0.5) + fwd * 0.05 - rt * 0.05).lerp(thL, smooth((f - 712) / 30.0))
    HP["place_hand"](pt, "L", f, l_pt, (-fwd + V(0, 0, -0.5)).normalized(), V(0, 0, -1), skin=0.02)
    for s_, o_ in (("L", -rt), ("R", rt)):
        shp = W(pt, "upperarm01." + s_); pole = shp + V(0, 0, -0.20) - fwd * 0.30 + o_ * 0.45
        pbp = pt.pose.bones["Pole_elbow." + s_]; pbp.location = pt.data.bones["Pole_elbow." + s_].matrix_local.to_3x3().inverted() @ (pole - pt.data.bones["Pole_elbow." + s_].head_local)
        pbp.keyframe_insert("location", frame=f, group=pbp.name)
    HP["apply_pose"](pt, "L", "relaxed", f)
for f, kw in ((641, dict(wide=0.3)), (700, dict(wide=0.3)), (712, dict(wide=0.45, brow=0.5, jaw=2, smile=-0.3)), (730, dict(close=0.45, brow=-0.5, jaw=2, smile=-0.6)),
              (750, dict(close=0.6, brow=-0.6, jaw=1.5, smile=-0.7)), (775, dict(close=0.55, brow=-0.5, jaw=2, smile=-0.6))):
    face(pt, f, **kw)
blink(pt, 672, dict(wide=0.3))
# liver glow INSIDE her abdomen: shirt and skin light up from a point inside her right upper belly
ge = OB.new("LiverGlowPt", None); bpy.data.collections["Home_Set"].objects.link(ge)
ev(704); ge.matrix_world = Matrix.Translation(W(pt, "spine02") + rt * 0.06 + fwd * 0.05)
gm = ge.matrix_world.copy(); ge.parent = pt; ge.parent_type = 'BONE'; ge.parent_bone = "spine02"; ge.matrix_world = gm
def add_glow(mat):
    nt = mat.node_tree; N, L = nt.nodes, nt.links
    out = [n for n in N if n.type == 'OUTPUT_MATERIAL' and n.is_active_output][0]; src = out.inputs['Surface'].links[0].from_socket
    tc = N.new("ShaderNodeTexCoord"); tc.object = ge
    mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1 / 0.085, 1 / 0.06, 1 / 0.11)
    L.new(tc.outputs["Object"], mp.inputs[0])
    ln = N.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'; L.new(mp.outputs[0], ln.inputs[0])
    mr = N.new("ShaderNodeMapRange"); mr.interpolation_type = 'SMOOTHSTEP'; L.new(ln.outputs["Value"], mr.inputs[0])
    mr.inputs[1].default_value = 1.6; mr.inputs[2].default_value = 0.5; mr.inputs[3].default_value = 0.0; mr.inputs[4].default_value = 1.0
    em = N.new("ShaderNodeEmission"); em.inputs[0].default_value = (1.0, 0.28, 0.08, 1); em.name = "LiverGlow"
    ml = N.new("ShaderNodeMath"); ml.operation = 'MULTIPLY'; L.new(mr.outputs[0], ml.inputs[0]); ml.name = "GlowAmt"
    L.new(ml.outputs[0], em.inputs[1])
    ad = N.new("ShaderNodeAddShader"); L.new(src, ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1]); L.new(ad.outputs[0], out.inputs['Surface'])
    for f, v in ((0, 0.0), (676, 0.0), (700, 0.6), (716, 1.6), (732, 2.2), (748, 1.7), (762, 2.6), (775, 2.4)):
        ml.inputs[1].default_value = v; ml.inputs[1].keyframe_insert("default_value", frame=f)
for m in set(OB["Patient.female_casualsuit01"].data.materials):
    if m.name.startswith("WomanTop"): add_glow(m)
VL.key_hide(OB["XRayLiver_Home"], [])

# =================================================================== S7: patient already on the bed at the cut (776)
ev(782); bed_pose = {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy()) for pb in pt.pose.bones}
for pb in pt.pose.bones:
    l_, q_ = bed_pose[pb.name]; pb.location = l_; pb.rotation_quaternion = q_
    pb.keyframe_insert("location", frame=776, group=pb.name); pb.keyframe_insert("rotation_quaternion", frame=776, group=pb.name)
clear_bones(pt, [pb.name for pb in pt.pose.bones], 777, 781)            # no in-between keys: on the bed from 776
VL.clear_keys(pt, ("delta_location",), 770, 790)
home = OB["Patient.female_casualsuit01"]; VL.key_hide(home, [(610, 1052)])        # her own top and jeans in bed too
c06 = OB.get("Patient.male_casualsuit06")
if c06: VL.key_hide(c06, [])
pbm = OB["Patient.body"]
for mn in ("Delete.male_casualsuit06",):
    mm_ = pbm.modifiers.get(mn)
    if mm_: VL.clear_keys(pbm, ('modifiers["%s"]' % mn,)); mm_.show_render = mm_.show_viewport = False
for mm_ in pbm.modifiers:
    if mm_.name.startswith("Delete.female_casualsuit01"):
        VL.clear_keys(pbm, ('modifiers["%s"]' % mm_.name,))
        for f_, on_ in ((0, False), (610, True), (1053, False)):
            mm_.show_render = on_; pbm.keyframe_insert('modifiers["%s"].show_render' % mm_.name, frame=f_)
VL.constant(pbm)
for o in (OB["Patient.ponytail01"], OB.get("Patient.shoes01")):
    if o: VL.key_hide(o, [(0, 1700)]) if o.name.endswith("ponytail01") else VL.key_hide(o, [(610, 1052)])
# 12: the nurse walks clear of the bed end and her hands grip the head-board rail
nu = OB["Nurse"]; br = OB["BedRig"]
for f_, dy in ((0, 0.0), (776, 0.16), (916, 0.0)):
    nu.delta_location = (0, dy, 0); nu.keyframe_insert("delta_location", frame=f_)
VL.constant(nu, ("delta_location",))
clear_bones(nu, ["IK_hand.L", "IK_hand.R"], 776, 915)
for f in range(776, 916, 3):
    ev(f)
    for s_, sx in (("L", -0.22), ("R", 0.22)):
        rail = br.matrix_world @ V(sx, 0.985, 0.85)
        HP["place_hand"](nu, s_, f, rail + V(0, 0.01, 0.012), V(0, -0.5, -0.85).normalized(), V(0, -1, -0.4).normalized(), skin=0.01)
        HP["apply_pose"](nu, s_, "wrap_grip", f)

# =================================================================== S8: new doctor's walk gets swinging arms; anaesthetist calm
s2 = OB["Surgeon2"]
s2p = {}
for f in range(879, 991):
    ev(f); s2p[f] = W(s2, "root").copy()
def s2yaw(f):
    a, b = s2p[max(879, f - 2)], s2p[min(990, f + 2)]; d = b - a
    return math.degrees(math.atan2(d.x, -d.y)) if d.length > 1e-4 else 0.0
dd = [0.0]
for f in range(880, 991): dd.append(dd[-1] + (s2p[f] - s2p[f - 1]).to_2d().length)
swing_arms("Surgeon2", 879, 984, s2yaw, lambda f: dd[min(len(dd) - 1, f - 879)] / 0.7, amp=0.12)
an = OB["Anaesth"]
clear_bones(an, ["IK_hand.L", "IK_hand.R", "Pole_elbow.L", "Pole_elbow.R"], -10, 2000)
cart = OB["AnesthesiaCart"]
ev(1)
for s, p in (("L", V(-1.30, 0.86, 1.155)), ("R", V(-1.29, 0.70, 1.155))):
    sh = W(an, "upperarm01." + s); fd = (p - sh); fd.z = 0; fd.normalize()
    for f in (1, 1644):
        HP["place_hand"](an, s, f, p, V(0, 0, -1), fd, skin=0.012); HP["apply_pose"](an, s, "relaxed", f)

# =================================================================== S9: second surgeon lifts the branded liver
E = OB["LiverRig"]; ev(1); E0 = E.matrix_world.copy()
LC = E0.translation.copy()
def liver_M(f):
    u = smooth((f - 1092) / 38.0); w = 0.004 * math.sin((f - 1130) / 9.0) if f > 1130 else 0.0
    T = Matrix.Translation(LC + V(0.01 * u, 0, 0.085 * u + w))
    Rr = Matrix.Rotation(R_(26 * u), 4, 'Y')
    return T @ Rr @ Matrix.Translation(-LC) @ E0
VL.clear_keys(E, ("location", "rotation_euler", "scale"))
E.rotation_mode = 'XYZ'
for f in [1] + list(range(1061, 1263, 2)):
    E.matrix_world = liver_M(f) if f >= 1061 else E0
    for p in ("location", "rotation_euler", "scale"): E.keyframe_insert(p, frame=f)
clear_bones(s2, ["IK_hand.L", "IK_hand.R", "Pole_elbow.L", "Pole_elbow.R"], 1040, 1262)
for f in range(1040, 1263, 2):
    M = liver_M(max(f, 1061)) @ E0.inverted()
    appr = 1.0 - smooth((f - 1040) / 40.0)                      # hands come in from above
    pr = M @ (LC + V(-0.062, -0.01, -0.012)); pl = M @ (LC + V(0.0, 0.088, -0.015))
    nr = (M.to_3x3() @ V(0.55, 0, 0.8)).normalized(); nl = (M.to_3x3() @ V(0, -0.55, 0.8)).normalized()
    pr = pr + V(-0.05, 0.06, 0.10) * appr; pl = pl + V(0.03, 0.08, 0.10) * appr
    ev(f)
    HP["place_hand"](s2, "R", f, pr, nr, (M.to_3x3() @ V(1, 0.15, 0)).normalized(), skin=0.002)
    HP["place_hand"](s2, "L", f, pl, nl, (M.to_3x3() @ V(0.15, -1, 0)).normalized(), skin=0.002)
    HP["apply_pose"](s2, "R", "cup_hold", f); HP["apply_pose"](s2, "L", "cup_hold", f)
# =================================================================== S10: her eyes widen (no frozen stare)
for f, kw in ((1150, dict(wide=0.3)), (1176, dict(wide=0.32, brow=0.2)), (1190, dict(wide=0.3, brow=0.7, jaw=2)), (1205, dict(wide=0.27, brow=0.6, jaw=1)),
              (1240, dict(wide=0.25, brow=0.45, jaw=1))):
    face(s2, f, **kw)
blink(s2, 1200, dict(wide=0.28, brow=0.65, jaw=1)); blink(s2, 1228, dict(wide=0.25, brow=0.5, jaw=1))
R2 = AL["Rig"](s2); clear_bones(s2, ["head", "neck02"], 1176, 1240)
for f_, p_, y_ in ((1176, 10, 0), (1190, -4, 3), (1206, -6, -5), (1222, -2, 4), (1240, 2, 0)):
    R2.key_rot("head", f_, [("X", p_ * 0.6), ("Z", y_)]); R2.key_rot("neck02", f_, [("X", p_ * 0.4)])
eyes(s2, 1176, 0, -6); eyes(s2, 1192, 0, -10); eyes(s2, 1200, 5, -4); eyes(s2, 1210, -4, -2); eyes(s2, 1226, 2, -8); eyes(s2, 1240, 0, -8)

# =================================================================== S11: hearing - hands rest on the lectern
for o in OB:                                          # lectern 15 cm further from him (his body was inside it)
    if o.name.startswith(("HEAR_Lectern",)) and o.parent is None: o.location.x -= 0.15
bpy.context.view_layer.update()
lt = OB["HEAR_LecternTop"]; lz = max((lt.matrix_world @ Vector(c)).z for c in lt.bound_box)
lxmax = max((lt.matrix_world @ Vector(c)).x for c in lt.bound_box)
clear_bones(s1, ["IK_hand.L", "IK_hand.R", "Pole_elbow.L", "Pole_elbow.R"], 1236, 1450)
for f in (1236, 1300, 1340, 1380, 1420, 1450):        # both hands rest on the lectern top (a slight weight shift only)
    ev(f)
    for s, sy in (("L", 0.20), ("R", -0.20)):
        sh_ = 0.01 * math.sin(f / 25.0) * (1 if s == "L" else -1)
        p = V(lxmax - 0.04 + sh_, sy * 0.85, lz + 0.004)
        hit = lt.ray_cast(lt.matrix_world.inverted() @ (p + V(0, 0, 0.5)), lt.matrix_world.inverted().to_3x3() @ V(0, 0, -1))
        if hit[0]: p.z = (lt.matrix_world @ hit[1]).z + 0.014
        HP["place_hand"](s1, s, f, p, V(0, 0, -1), V(-1, -0.25 if s == "L" else 0.25, 0).normalized(), skin=0.012)
        HP["apply_pose"](s1, s, "relaxed", f)
        sh = W(s1, "upperarm01." + s); pole = sh + V(0.35, 0.25 * (1 if s == "L" else -1), -0.35)
        pbp = s1.pose.bones["Pole_elbow." + s]; pbp.location = s1.data.bones["Pole_elbow." + s].matrix_local.to_3x3().inverted() @ (pole - s1.data.bones["Pole_elbow." + s].head_local)
        pbp.keyframe_insert("location", frame=f, group=pbp.name)
for f, kw in ((1241, dict(wide=0.3, brow=-0.2)), (1300, dict(wide=0.25, brow=0.3, jaw=3)), (1360, dict(wide=0.2, brow=0.4)), (1445, dict(wide=0.2, brow=0.2))):
    face(s1, f, **kw)
blink(s1, 1280, dict(wide=0.28, brow=0.1)); blink(s1, 1390, dict(wide=0.2, brow=0.4))

# =================================================================== S12: the judge grips the gavel and strikes the block
# desk top ended behind the seated panel (their bodies went through it): back edge now in front of them
dt = OB["HEAR_DeskTop"]; mwi = dt.matrix_world.inverted()
for v in dt.data.vertices:
    w = dt.matrix_world @ v.co
    if w.x < -10.24: w.x = -10.24; v.co = mwi @ w
dt.data.update()
ja = OB["PanelA"]; gv = OB["Gavel"]; blk = OB["Gavel_src_4"]
VL.key_hide(OB["HEAR_Glass.001"], [])          # no glass in front of the judge's block (it never moves either)
ev(1); G0 = Matrix.Translation(V(0.10, 0, 0)) @ gv.matrix_world.copy()   # on the desk (moved forward with the trimmed desk edge)
_gp = G0.translation.copy(); G0 = Matrix.Translation(_gp + V(0.04, -0.06, 0)) @ Matrix.Rotation(R_(65), 4, 'Z') @ Matrix.Translation(-_gp) @ G0   # v014: handle across his grip
VL.clear_keys(gv, ("location", "rotation_quaternion", "rotation_euler"))
gv.rotation_mode = 'QUATERNION'; gv.matrix_world = G0; ev(1446)
head_pts = [o.matrix_world @ Vector(c) for o in (OB["Gavel_src_0"], OB["Gavel_src_1"], OB["Gavel_src_2"]) for c in o.bound_box]
hc = sum(head_pts, Vector()) / len(head_pts); hbot = min(p.z for p in head_pts)
bpts = [blk.matrix_world @ Vector(c) for c in blk.bound_box]; btop = max(p.z for p in bpts); bc = sum(bpts, Vector()) / 8
hpts = [OB["Gavel_src_3"].matrix_world @ Vector(c) for c in OB["Gavel_src_3"].bound_box]
grip = V(min(p.x for p in hpts) + 0.06, sum(p.y for p in hpts) / 8, sum(p.z for p in hpts) / 8)
strike_T = Matrix.Translation(V(bc.x - hc.x, bc.y - hc.y, btop - hbot + 0.001))
axis = (V(hc.x, hc.y, 0) - V(grip.x, grip.y, 0)).normalized().cross(V(0, 0, 1))
def gpose(lift, ang, base=strike_T):
    g = base @ G0; gp = (base @ Matrix.Translation(grip)).translation
    return Matrix.Translation(gp + V(0, 0, lift)) @ Matrix.Rotation(R_(ang), 4, axis) @ Matrix.Translation(-gp) @ g
FP = 1478
GK = [(1446, None), (FP, G0), (1490, gpose(0.06, -10, Matrix.Translation(V(0, 0, 0.02)))), (1504, gpose(0.16, -38)), (1512, gpose(0.17, -45)),
      (1519, gpose(0.0, 0)), (1524, gpose(0.035, -8)), (1532, gpose(0.0, 0)), (1546, gpose(0.07, -16)), (1575, gpose(0.08, -18))]
def gmat(f):
    if f <= FP: return G0
    for (fa, Ma), (fb, Mb) in zip(GK[1:], GK[2:]):
        if fa <= f <= fb:
            u = (f - fa) / (fb - fa); u = u * u if fb in (1519, 1532) else smooth(u)          # accelerate into the strike
            la, qa, _ = Ma.decompose(); lb, qb, _ = Mb.decompose()
            return Matrix.Translation(la.lerp(lb, u)) @ qa.slerp(qb, u).to_matrix().to_4x4()
    return GK[-1][1]
clear_bones(ja, ["IK_hand.R", "Pole_elbow.R"], 1446, 1576)
ev(FP)
hd_ = (grip - W(ja, "upperarm01.R")); hd_.z = 0
HP["grip_object"](ja, "R", FP, OB["Gavel_src_3"], grip, V(0, 0, -1))
ev(FP); Hrel = G0.inverted() @ (ja.matrix_world @ ja.pose.bones["IK_hand.R"].matrix)
fing = {pb.name: pb.rotation_quaternion.copy() for pb in ja.pose.bones if pb.name.startswith("finger") and pb.name.endswith(".R")}
ev(1446); restH = (ja.matrix_world @ ja.pose.bones["IK_hand.R"].matrix).copy()
for f in range(1446, 1576):
    gm_ = gmat(f)
    if f >= FP:
        Mh = ja.matrix_world.inverted() @ gm_ @ Hrel
    else:
        u = smooth((f - 1446) / (FP - 1446)); Ma = ja.matrix_world.inverted() @ restH; Mb = ja.matrix_world.inverted() @ G0 @ Hrel
        la, qa, _ = Ma.decompose(); lb, qb, _ = Mb.decompose(); Mh = Matrix.Translation(la.lerp(lb, u) + V(0, 0, 0.05 * math.sin(math.pi * u))) @ qa.slerp(qb, u).to_matrix().to_4x4()
    pb = ja.pose.bones["IK_hand.R"]; pb.matrix = Mh
    pb.keyframe_insert("location", frame=f, group=pb.name); pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
    gv.matrix_world = gm_; gv.keyframe_insert("location", frame=f); gv.keyframe_insert("rotation_quaternion", frame=f)
    if f >= FP - 4:
        for n, q in fing.items():
            pbf = ja.pose.bones[n]; pbf.rotation_quaternion = q; pbf.keyframe_insert("rotation_quaternion", frame=f, group=n)
gv.matrix_world = G0; gv.keyframe_insert("location", frame=1); gv.keyframe_insert("rotation_quaternion", frame=1)
for f, kw in ((1446, dict(wide=0.3, brow=-0.3)), (1500, dict(wide=0.25, brow=-0.5, jaw=2)), (1519, dict(wide=0.35, brow=-0.4)), (1575, dict(wide=0.3, brow=-0.3))):
    face(ja, f, **kw)
blink(ja, 1470, dict(wide=0.3, brow=-0.3))

# =================================================================== S13: the clerk stamps a red X
cl = OB["PanelB"]; st = OB["Stamp"]
ev(1); S0 = st.matrix_world.copy()                       # where it stands on the desk
VL.clear_keys(st, ("location", "rotation_euler", "rotation_quaternion"))
st.rotation_mode = 'QUATERNION'; st.matrix_world = S0; ev(1576)
for o in OB:
    if o.name.startswith(("Certificate", "CertLine", "CertSeal", "CertBorder")) and o.parent is None: o.location += V(0.05, -0.20, 0)
bpy.context.view_layer.update()
cert = OB["Certificate"]; cpts = [cert.matrix_world @ Vector(c) for c in cert.bound_box]; cc = sum(cpts, Vector()) / 8; ctop = max(p.z for p in cpts)
bpts = [OB["StampBase"].matrix_world @ Vector(c) for c in OB["StampBase"].bound_box]; sbot = min(p.z for p in bpts); sbc = sum(bpts, Vector()) / 8
press = Matrix.Translation(V(cc.x - sbc.x + 0.01, cc.y - sbc.y, ctop - sbot + 0.0015)) @ S0
up = lambda M, h: Matrix.Translation(V(0, 0, h)) @ M
SP = 1592
SK = [(SP, S0), (1602, up(S0, 0.09)), (1610, up(press, 0.06)), (1616, press), (1620, press), (1627, up(press, 0.06)), (1634, up(Matrix.Translation(V(0.02, -0.15, 0)) @ press, 0.05)), (1640, Matrix.Translation(V(0.02, -0.15, -0.0015)) @ press), (1644, Matrix.Translation(V(0.02, -0.15, -0.0015)) @ press)]   # v013: set down beside the certificate
def smat(f):
    if f <= SP: return S0
    for (fa, Ma), (fb, Mb) in zip(SK, SK[1:]):
        if fa <= f <= fb:
            u = smooth((f - fa) / (fb - fa)); la, qa, _ = Ma.decompose(); lb, qb, _ = Mb.decompose()
            return Matrix.Translation(la.lerp(lb, u)) @ qa.slerp(qb, u).to_matrix().to_4x4()
    return SK[-1][1]
hpts = [OB["StampHandle"].matrix_world @ Vector(c) for c in OB["StampHandle"].bound_box]; hcen = sum(hpts, Vector()) / 8
clear_bones(cl, ["IK_hand.R", "Pole_elbow.R"], 1560, 1700)
ev(SP)
ap = hcen - W(cl, "upperarm01.R"); ap.z = 0
HP["grip_object"](cl, "R", SP, OB["StampHandle"], hcen, ap.normalized())
ev(SP); Hs = S0.inverted() @ (cl.matrix_world @ cl.pose.bones["IK_hand.R"].matrix)
fing = {pb.name: pb.rotation_quaternion.copy() for pb in cl.pose.bones if pb.name.startswith("finger") and pb.name.endswith(".R")}
ev(1576); restS = (cl.matrix_world @ cl.pose.bones["IK_hand.R"].matrix).copy()
for f in range(1560, 1645):
    sm = smat(f)
    if f >= SP: Mh = cl.matrix_world.inverted() @ sm @ Hs
    else:
        u = smooth((f - 1576) / (SP - 1576)); Ma = cl.matrix_world.inverted() @ restS; Mb = cl.matrix_world.inverted() @ S0 @ Hs
        la, qa, _ = Ma.decompose(); lb, qb, _ = Mb.decompose(); Mh = Matrix.Translation(la.lerp(lb, u) + V(0, 0, 0.04 * math.sin(math.pi * u))) @ qa.slerp(qb, u).to_matrix().to_4x4()
    pb = cl.pose.bones["IK_hand.R"]; pb.matrix = Mh
    pb.keyframe_insert("location", frame=f, group=pb.name); pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
    st.matrix_world = sm; st.keyframe_insert("location", frame=f); st.keyframe_insert("rotation_quaternion", frame=f)
    if f >= SP - 3:
        for n, q in fing.items():
            pbf = cl.pose.bones[n]; pbf.rotation_quaternion = q; pbf.keyframe_insert("rotation_quaternion", frame=f, group=n)
st.matrix_world = S0; st.keyframe_insert("location", frame=1); st.keyframe_insert("rotation_quaternion", frame=1)
# red X (no text): two crossed ink bars printed where the stamp came down
for o in [OB["StampMark"]] + list(OB["StampMark"].children): VL.key_hide(o, [])
M_INK = bpy.data.materials.new("StampInk"); M_INK.use_nodes = True
bi = M_INK.node_tree.nodes["Principled BSDF"]; bi.inputs["Base Color"].default_value = (0.55, 0.0, 0.0, 1); bi.inputs["Roughness"].default_value = 0.5
bi.inputs["Emission Color"].default_value = (0.6, 0.0, 0.0, 1); bi.inputs["Emission Strength"].default_value = 0.4
pz = (press @ S0.inverted() @ Matrix.Translation(sbc)).translation
for a in (45, -45):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); me = bpy.data.meshes.new("RedX"); bm.to_mesh(me); bm.free()
    ob = OB.new("RedX", me); bpy.data.collections["Hearing_Set"].objects.link(ob); me.materials.append(M_INK)
    ob.scale = (0.11, 0.022, 0.0008); ob.rotation_euler = (0, 0, R_(a)); ob.location = V(pz.x, pz.y, ctop + 0.0007)
    VL.key_hide(ob, [(1619, 1700)])
for f, kw in ((1576, dict(wide=0.3)), (1600, dict(wide=0.3, brow=-0.2)), (1616, dict(wide=0.25, brow=-0.3, jaw=2)), (1644, dict(wide=0.3, smile=0.1))):
    face(cl, f, **kw)
blink(cl, 1585, dict(wide=0.3)); blink(cl, 1636, dict(wide=0.3, smile=0.1))
eyes(cl, 1576, 0, -8); eyes(cl, 1600, -6, -14); eyes(cl, 1630, 0, -12); eyes(cl, 1644, 4, -2)


# =================================================================== v013 extras
# bed shot: the second surgeon walks beside the bed, attending her (visible from the bed shot on)
for o in rig_objs("Surgeon2"):
    for fc in VL.fcurves(o):
        if fc.data_path == "hide_render":
            for kp in fc.keyframe_points:
                if 870 <= kp.co.x <= 880 and kp.co.y < 0.5: kp.co.x = 776
            fc.update()
s2b = lambda f: V(2.42, 6.05, 0).lerp(V(2.42, 3.85, 0), smooth((f - 776) / 139.0) * 0.3 + 0.7 * (f - 776) / 139.0)
walk("Surgeon2", s2b, 776, 915, stride=0.62, amp=0.11, out_k=0.08)
clear_bones(s2, ["IK_hand.L", "IK_hand.R", "Pole_elbow.L", "Pole_elbow.R"], 985, 1039)
for f in range(986, 1040, 3):
    ev(f); s2sh = {sv: W(s2, "upperarm01." + sv) for sv in "LR"}; fw2 = V(0, -1, 0)
    for sv in "LR":
        q = s2sh[sv] + fw2 * 0.28; q.z = 2.0
        h_ = OB["DrapeFit"].ray_cast(OB["DrapeFit"].matrix_world.inverted() @ q, OB["DrapeFit"].matrix_world.inverted().to_3x3() @ V(0, 0, -1))
        tgt = V(q.x, q.y, ((OB["DrapeFit"].matrix_world @ h_[1]).z if h_[0] else 1.05) + 0.012)
        k = smooth((f - 986) / 24.0); hang = s2sh[sv] + V(0, 0, -0.5) + fw2 * 0.08
        HP["place_hand"](s2, sv, f, hang.lerp(tgt, k), V(0, 0, -1), (fw2 + V(0, 0, -0.6 * (1 - k))).normalized(), skin=0.012)
        HP["apply_pose"](s2, sv, "relaxed", f)
        oo = (s2sh[sv] - s2sh["L" if sv == "R" else "R"]).normalized()
        pbp = s2.pose.bones["Pole_elbow." + sv]; pole = s2sh[sv] + V(0, 0, -0.3) - fw2 * 0.3 + oo * 0.3
        pbp.location = s2.data.bones["Pole_elbow." + sv].matrix_local.to_3x3().inverted() @ (pole - s2.data.bones["Pole_elbow." + sv].head_local)
        pbp.keyframe_insert("location", frame=f, group=pbp.name)
swing_arms("Surgeon2", 916, 984, s2yaw, lambda f: dd[min(len(dd) - 1, f - 879)] / 0.7, amp=0.10)   # re-key from the cut (no hands sliding from the corridor)
for f, kw in ((776, dict(wide=0.3, brow=0.2)), (840, dict(wide=0.3, brow=0.3)), (915, dict(wide=0.3, brow=0.2))):
    face(s2, f, **kw)
blink(s2, 812, dict(wide=0.3, brow=0.25)); eyes(s2, 776, 18, -12); eyes(s2, 850, 10, -10); eyes(s2, 900, 0, -4)
# hearing wide: the panel talks / reacts
RP = {n: AL["Rig"](OB[n]) for n in ("PanelA", "PanelB", "PanelC")}
for f in range(1241, 1311, 6):
    face(OB["PanelA"], f, wide=0.3, brow=-0.2, jaw=(4 if (f // 6) % 2 else 0.5))
for n, ph in (("PanelB", 0.0), ("PanelC", 1.3)):
    clear_bones(OB[n], ["head"], 1236, 1312)
    for f in range(1241, 1312, 10):
        RP[n].key_rot("head", f, [("X", 6 * math.sin(f / 9.0 + ph)), ("Z", 8 * math.sin(f / 14.0 + ph))])
blink(OB["PanelB"], 1262, dict(wide=0.3)); blink(OB["PanelC"], 1290, dict(wide=0.3)); blink(OB["PanelA"], 1276, dict(wide=0.3, brow=-0.2))
# defendant admits it: he speaks (jaw), brows, blinks, small head moves
for f in range(1311, 1446, 5):
    face(s1, f, wide=0.28, brow=0.25 + 0.15 * math.sin(f / 11.0), jaw=(5 if (f // 5) % 2 else 1), smile=0.15 * math.sin(f / 17.0))
blink(s1, 1330, dict(wide=0.28, brow=0.3)); blink(s1, 1372, dict(wide=0.28, brow=0.3)); blink(s1, 1418, dict(wide=0.28, brow=0.3))
clear_bones(s1, ["head", "neck02"], 1311, 1445)
for f in range(1311, 1446, 15):
    R1.key_rot("head", f, [("X", -4 + 5 * math.sin(f / 13.0)), ("Z", 7 * math.sin(f / 21.0))])
# one liver graphic behind him (not a repeated row)
for k in (0, 2, 3, 4):
    g_ = OB.get("GhostLiver_%d" % k)
    if g_: VL.key_hide(g_, [])
# the judge's left hand lies flat on the desk (no hovering hand)
clear_bones(ja, ["IK_hand.L", "Pole_elbow.L"], 1440, 1580)
dtop = max((dt.matrix_world @ v.co).z for v in dt.data.vertices)
for f in (1440, 1500, 1580):
    ev(f); HP["place_hand"](ja, "L", f, V(-10.08, 0.24, dtop), V(0, 0, -1), V(1, 0.1, 0).normalized(), skin=0.012); HP["apply_pose"](ja, "L", "relaxed", f)
# no glass in front of the clerk's camera
for n in ("HEAR_Glass", "HEAR_Glass.002"):
    if OB.get(n): VL.key_hide(OB[n], [])

bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("ANIM_DONE", OUT)
