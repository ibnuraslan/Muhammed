"""WaterTubes blocking/polish animation: people, flood timing, debris, cutaway swaps, explainer, one continuous camera.
blender -b set.blend --python 03_animate.py -- <people.blend> <out.blend>"""
import sys, os, math, random
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler
HERE = os.path.dirname(os.path.abspath(__file__))
a = sys.argv[sys.argv.index("--") + 1:]
PEOPLE, OUT = a[0], a[1]
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
random.seed(7)
sc = bpy.context.scene
FPS = 60
def F(t): return 1 + round(t * FPS)

# ------------------------------------------------------------------ ground height: lawn/street + hero porch and steps (ray cast)
_G = bpy.data.objects["Ground"]; _H = bpy.data.objects["HeroHouse"]
def ground_z(x, y):
    best = -1.0
    for ob in (_G, _H):
        mi = ob.matrix_world.inverted()
        hit, loc, nrm, idx = ob.ray_cast(mi @ Vector((x, y, 1.6)), (mi.to_3x3() @ Vector((0, 0, -1))).normalized())
        if hit:
            z = (ob.matrix_world @ loc).z
            if ob is _H and z > 1.45: continue
            best = max(best, z)
    if -20.2 < y < -11.8 and best < -0.1: best = -0.12
    return max(best, -0.14)
globals()["ground_z"] = ground_z

def kv(owner, path, f, v, interp=None):
    setattr(owner, path, v) if not path.startswith("[") else None
    owner.keyframe_insert(path, frame=f)
def ksock(sock, f, v):
    sock.default_value = v; sock.keyframe_insert("default_value", frame=f)
def khide(ob, ranges):
    """hide_render/visibility keyed: visible only inside the given frame ranges"""
    ob.hide_render = True; ob.keyframe_insert("hide_render", frame=1)
    for f0, f1 in ranges:
        ob.hide_render = False; ob.keyframe_insert("hide_render", frame=f0)
        ob.hide_render = True; ob.keyframe_insert("hide_render", frame=f1)
    if ob.animation_data and ob.animation_data.action:
        for fc in _fcurves(ob.animation_data.action):
            for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"
def _fcurves(act):
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []): out += list(cb.fcurves)
    return out or list(getattr(act, "fcurves", []))

# ------------------------------------------------------------------ flood timeline
FG = bpy.data.node_groups["FloodSurface"]; FN = FG.nodes
# hero-zone lag: spread boost away from the hero lot (|x| > 11) so the neighbours flood first and the ring is hit on beat 7
N, L = FG.nodes, FG.links
boost = N.new("ShaderNodeValue"); boost.name = "Boost"; boost.outputs[0].default_value = 0.0
# find the SpreadY usage (ADD node fed by SpreadY with 0.0) and add boost * smoothstep(|x|)
add_node = next(n for n in N if n.type == "MATH" and n.operation == "ADD" and n.inputs[0].links and n.inputs[0].links[0].from_node.name == "SpreadY")
sepx = next(n for n in N if n.type == "SEPXYZ")
ab = N.new("ShaderNodeMath"); ab.operation = "ABSOLUTE"; L.new(sepx.outputs["X"], ab.inputs[0])
mr = N.new("ShaderNodeMapRange"); mr.interpolation_type = "SMOOTHSTEP"; mr.inputs["From Min"].default_value = 11.5; mr.inputs["From Max"].default_value = 17.0
L.new(ab.outputs[0], mr.inputs["Value"])
mu = N.new("ShaderNodeMath"); mu.operation = "MULTIPLY"; L.new(mr.outputs[0], mu.inputs[0]); L.new(boost.outputs[0], mu.inputs[1])
L.new(mu.outputs[0], add_node.inputs[1])
def flood(name, keys):
    s = FN[name].outputs[0]
    for f, v in keys: ksock(s, f, v)
FRONT = [(1, 140), (F(8.3), 62), (F(9.3), 34), (F(10.3), 12), (F(11.3), -14), (F(13.0), -60), (F(15), -100)]
flood("FrontX", FRONT)
flood("SpreadY", [(1, 4.4), (F(10.0), 4.6), (F(12.0), 5.0), (F(20.8), 5.2), (F(21.3), 6.6), (F(21.6), 7.9), (F(22.4), 12), (F(23.4), 40)])
flood("Boost", [(1, 0), (F(10.6), 0), (F(12.4), 16), (F(23.4), 0)])
flood("Level", [(1, 0.3), (F(9.5), 0.4), (F(12.5), 0.5), (F(21.0), 0.55), (F(21.6), 0.66), (F(24.5), 0.62), (F(26.4), 0.36), (F(28.0), 0.3), (F(33.5), 0.28)])
flood("Lip", [(1, 1.0), (F(11.0), 0.9), (F(12.4), 0.4), (F(20.8), 0.3), (F(21.5), 1.0), (F(22.8), 0.35), (F(24.5), 0.05)])
flood("Chop", [(1, 0.07), (F(21.4), 0.1), (F(24.5), 0.05), (F(27.0), 0.02)])
fl = bpy.data.objects["Flood"]
khide(fl, [(1, F(15.0)), (F(20.85), 2011)])          # hidden while inside the cutaway shell
# mud after the flood
gm = bpy.data.materials["GroundMix"].node_tree.nodes["MudAmount"].outputs[0]
ksock(gm, F(24.5), 0.0); ksock(gm, F(26.0), 1.0)
for m in bpy.data.materials:
    if m.node_tree and "MudLine" in m.node_tree.nodes:
        s = m.node_tree.nodes["MudLine"].outputs[0]; ksock(s, F(24.0), -0.5); ksock(s, F(24.1), 0.64)

def level_at(f):
    """approx water surface z at frame f in the flooded street (for floating debris)"""
    sc.frame_set(f); return FN["Level"].outputs[0].default_value
def front_at(f):
    sc.frame_set(f); return FN["FrontX"].outputs[0].default_value

# ------------------------------------------------------------------ cutaway swap + shell + explainer
sh_mix = bpy.data.materials["CutBackdrop"].node_tree.nodes["ShellFade"].inputs["Fac"]
for f, v in ((1, 0), (F(14.6) - 6, 0), (F(14.6) + 8, 1), (F(20.6), 1), (F(20.95), 0)): ksock(sh_mix, f, v)
CUT_IN, CUT_OUT = F(14.6), F(20.85)
khide(bpy.data.objects["CutShell"], [(F(14.6) - 8, F(21.0))])
for n in ("Tube_0", "Valve_0"):
    khide(bpy.data.objects[n], [(1, CUT_IN), (CUT_OUT, 2011)])
for n in ["CutTube", "CutWater", "CutKey", "CutRim"] + [o.name for o in bpy.data.objects if o.name.startswith("Bubble_")]:
    khide(bpy.data.objects[n], [(CUT_IN, CUT_OUT)])
# the hose is removed once the tube is full (he unscrews it and coils it at the reel) -> keep it only in beats 1-2
khide(bpy.data.objects["Hose"], [(1, F(8.4))]); khide(bpy.data.objects["Nozzle"], [(1, F(8.4))])
# water in the section sags and settles (weight)
cw, ct = bpy.data.objects["CutWater"], bpy.data.objects["CutTube"]
# scale about the tube axis: parent both to an empty at the tube centre line
piv = bpy.data.objects.new("CutPivot", None); sc.collection.objects.link(piv); piv.location = (0, -9.0, 0.0); bpy.context.view_layer.update()
for ob in (cw, ct):
    ob.parent = piv; ob.matrix_parent_inverse = piv.matrix_world.inverted()
for f, sz, sy in ((CUT_IN, 1.0, 1.0), (F(15.6), 0.955, 1.03), (F(16.2), 0.975, 1.012), (F(17.0), 0.96, 1.025), (F(19.4), 0.93, 1.045), (F(20.0), 0.95, 1.03)):
    piv.scale = (1, sy, sz); piv.keyframe_insert("scale", frame=f)
# flood wall pushes in, arrows grow and strain, the weight arrow presses down and wins
fw = bpy.data.objects["FloodWall"]
khide(fw, [(F(17.0), CUT_OUT)])
for o in [o for o in bpy.data.objects if o.name.startswith("Silt_")]: khide(o, [(F(17.0), CUT_OUT)])
for f, y in ((F(17.0), -12.6), (F(17.9), -11.05), (F(18.6), -11.15), (F(19.0), -11.0), (F(20.6), -11.05)):
    fw.location.y = y; fw.keyframe_insert("location", index=1, frame=f)
for i in range(3):
    ar = bpy.data.objects[f"FloodArrow_{i}"]; khide(ar, [(F(17.3) + 6 * i, CUT_OUT - 10)])
    base = ar.location.copy()
    for f, s_, dy in ((F(17.3) + 6 * i, 0.05, -0.4), (F(17.9) + 6 * i, 1.0, 0.0), (F(18.5), 1.08, 0.06), (F(18.8), 1.0, 0.0), (F(19.3), 0.95, -0.05),
                      (F(19.8), 0.7, -0.25), (F(20.4), 0.55, -0.35)):
        ar.scale = (s_, s_, s_); ar.keyframe_insert("scale", frame=f)
        ar.location = base + Vector((0, dy, 0)); ar.keyframe_insert("location", frame=f)
wa = bpy.data.objects["WeightArrow"]; khide(wa, [(F(18.6), CUT_OUT - 6)]); wb = wa.location.copy()
for f, s_, dz in ((F(18.6), 0.05, 0.5), (F(19.1), 1.0, 0.0), (F(19.35), 1.2, -0.08), (F(19.6), 1.1, -0.03), (F(20.4), 1.15, -0.05)):
    wa.scale = (s_, s_, s_); wa.keyframe_insert("scale", frame=f); wa.location = wb + Vector((0, 0, dz)); wa.keyframe_insert("location", frame=f)

# ------------------------------------------------------------------ people
with bpy.data.libraries.load(PEOPLE) as (src, dst): dst.objects = src.objects
for o in dst.objects: sc.collection.objects.link(o)
C_PEOPLE = bpy.data.collections.new("People"); sc.collection.children.link(C_PEOPLE)
for o in dst.objects:
    for u in list(o.users_collection): u.objects.unlink(o)
    C_PEOPLE.objects.link(o)
RIG = {n: bpy.data.objects[n] for n in ("Hero", "NeighbourA", "NeighbourB")}
ASSETS = os.path.join(HERE, "..", "assets")
for img in bpy.data.images:
    for nm in ("male_casualsuit02_diffuse", "female_casualsuit02_diffuse"):
        if img.name.startswith(nm):
            img.filepath = os.path.join(ASSETS, nm + "_noprint.png"); img.reload()
mA = bpy.data.objects["NeighbourA.female_casualsuit02"].data.materials[0]
for nd in list(mA.node_tree.nodes):
    if nd.type == "TEX_IMAGE" and "diffuse" in nd.image.name.lower():
        for lk in list(nd.outputs["Color"].links):
            hs = mA.node_tree.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Hue"].default_value = 0.88; hs.inputs["Saturation"].default_value = 0.8
            mA.node_tree.links.new(nd.outputs["Color"], hs.inputs["Color"]); mA.node_tree.links.new(hs.outputs[0], lk.to_socket)
CT, HU = {}, {}
for n, ob in RIG.items():
    CT[n] = make_human_ctrl(ob); HU[n] = Human(CT[n])
def limit(pb, x, y, z):
    c = pb.constraints.new("LIMIT_ROTATION"); c.owner_space = "LOCAL"; c.use_transform_limit = True
    c.use_limit_x = c.use_limit_y = c.use_limit_z = True
    c.min_x, c.max_x = R_(x[0]), R_(x[1]); c.min_y, c.max_y = R_(y[0]), R_(y[1]); c.min_z, c.max_z = R_(z[0]), R_(z[1])
for n, ob in RIG.items():
    for pb in ob.pose.bones:
        nm = pb.name
        if nm.startswith("finger1-"): limit(pb, (-30, 60), (-35, 35), (-35, 35))
        elif nm.startswith("finger"): limit(pb, (-2, 90), (-10, 10), (-10, 10))
        elif nm.startswith("wrist."): limit(pb, (-60, 60), (-45, 45), (-25, 25))
def HOLD(n, s, f):
    return (n == "Hero" and s == "R" and f <= F(8.35)) or (n == "NeighbourA" and F(0.3) <= f <= F(7.6))
def arms(h, n, f, pos, yaw, mode="hang", phase=0.0, amp=0.0):
    """hand targets relative to the body: hang (with walk swing), hips, chest(crossed), head, up, out"""
    r = h.r; B = r.BN
    Ry = Matrix.Rotation(R_(yaw), 3, "Z")
    root = h.root_head
    for s in "LR":
        sx = 1 if s == "L" else -1
        sh = B["upperarm01." + s].head_local
        sw = amp * math.sin(2 * math.pi * phase + (0 if s == "L" else math.pi))
        k = sh.z / 1.433   # body scale
        wide = {"NeighbourB": 0.06, "NeighbourA": 0.025}.get(n, 0.0)
        if mode == "hang":   W = sh + k * Vector((sx * 0.085, -0.05 + 0.2 * sw, -0.46)); d = Vector((sx * 0.15, -0.15, -1)); nn = Vector((-sx, 0, 0))
        elif mode == "hips": W = sh + k * Vector((sx * 0.12, -0.02, -0.36)); d = Vector((-sx * 0.15, -0.3, -0.6)); nn = Vector((-sx, 0.2, 0))
        elif mode == "chest": W = sh + k * Vector((sx * 0.06, -0.27, -0.4)); d = Vector((sx * 0.05, -0.7, -0.7)); nn = Vector((-sx, 0, 0))
        elif mode == "head":
            hc = r.BN["head"].head_local + Vector((0, 0.05, 0.15)) * k         # hands on the top-sides of the head, palms in, behind the face
            d = Vector((-sx * 0.35, 0.3, 0.9)); nn = Vector((-sx, 0, -0.3))
            W = hc + Vector((sx * 0.118 * k, 0.0, 0.012)) - d.normalized() * 0.085 * k
        elif mode == "up":   W = sh + k * Vector((sx * 0.1, -0.36, -0.02)); d = Vector((sx * 0.05, -0.15, 1.0)); nn = Vector((0, -1, 0.1))
        elif mode == "out":  W = sh + k * Vector((sx * 0.3, -0.22, -0.34)); d = Vector((sx * 0.6, -0.5, -0.5)); nn = Vector((0, 0.3, -1))
        elif mode == "brow": W = (sh + k * Vector((-sx * 0.1, -0.32, 0.22))) if s == "L" else (sh + k * Vector((sx * 0.085, -0.05, -0.46))); d = Vector((-sx, -0.2, 0.3)) if s == "L" else Vector((sx * 0.1, -0.15, -1)); nn = Vector((0, 1, -0.4)) if s == "L" else Vector((-sx, 0, 0))
        if mode in ("hang", "hips", "chest", "brow", "head"): W = W + Vector((sx * wide, 0, 0))
        # body space -> world via root transform
        Wl = W - Vector((root.x, root.y, 0.0))
        base = Vector((pos.x, pos.y, ground_z(pos.x, pos.y)))
        Ww = base + Ry @ Wl
        if not HOLD(n, s, f): grip(h.r.o, s, f, {"head": 0.3, "up": 0.15, "out": 0.25, "brow": 0.3, "hips": 0.35}.get(mode, 0.3))
        h.key_hand(s, f, Ww, Ry @ d, Ry @ nn, pole=base + Ry @ (B["lowerarm01." + s].head_local - Vector((root.x, root.y, 0.0)) + (Vector((sx * 0.6, 0.1, 0.45)) if mode in ("head", "up") else Vector((sx * 0.3, 0.4, -0.1)))))
def stand(h, f, pos, yaw, flex=0.0, crouch=0.0, side=0.0, head=(0, 0), twist=0.0, feet=None):
    gz = ground_z(pos.x, pos.y)
    h.key_root(f, Vector((pos.x, pos.y, gz + h.root_head.z - crouch)), yaw=yaw, flex=flex * 0.4, side=side)
    h.key_spine(f, flex=flex, twist=twist, head=head)
    for s in "LR":
        xy = feet[s] if feet else h.foot_xy(s, pos, yaw)
        h.key_foot(s, f, xy, yaw)
def face(rig, f, brow=0.0, jaw=0.0, lids=0.0, smile=0.0):
    """MPFB face bones: brow raise (oculi), jaw drop, lids wide (orbicularis), mouth corners (risorius)"""
    P = rig.pose.bones
    for s in "LR":
        for b in ("oculi01.", "oculi02."):
            pb = P[b + s]; pb.rotation_mode = "XYZ"; pb.location = (0, brow * 0.006, 0); pb.keyframe_insert("location", frame=f)
        pb = P["orbicularis03." + s]; pb.rotation_mode = "XYZ"; pb.rotation_euler = (R_(lids * 12), 0, 0); pb.keyframe_insert("rotation_euler", frame=f)
        pb = P["orbicularis04." + s]; pb.rotation_mode = "XYZ"; pb.rotation_euler = (R_(-lids * 6), 0, 0); pb.keyframe_insert("rotation_euler", frame=f)
        pb = P["risorius03." + s]; pb.location = (0, smile * 0.004, 0); pb.keyframe_insert("location", frame=f)
    pb = P["jaw"]; pb.rotation_mode = "XYZ"; pb.rotation_euler = (R_(jaw * 16), 0, 0); pb.keyframe_insert("rotation_euler", frame=f)

def grip(rig, s, f, amt):
    """curl fingers (local X) for a grasp; amt 0 open .. 1 fist"""
    P = rig.pose.bones
    for fi in range(2, 6):
        for j in range(1, 4):
            pb = P.get(f"finger{fi}-{j}.{s}")
            if pb: pb.rotation_mode = "XYZ"; pb.rotation_euler = (R_(amt * (48 if j == 1 else 62)), 0, 0); pb.keyframe_insert("rotation_euler", frame=f)
    sx = 1 if s == "L" else -1
    pb = P.get(f"finger1-1.{s}")
    if pb: pb.rotation_mode = "XYZ"; pb.rotation_euler = (R_(amt * 20), 0, R_(-sx * amt * 25)); pb.keyframe_insert("rotation_euler", frame=f)
    for j in (2, 3):
        pb = P.get(f"finger1-{j}.{s}")
        if pb: pb.rotation_mode = "XYZ"; pb.rotation_euler = (R_(amt * 30), 0, 0); pb.keyframe_insert("rotation_euler", frame=f)
for n in RIG:
    for s in "LR": grip(RIG[n], s, 1, 0.3)
H = HU["Hero"]; HR = RIG["Hero"]
VALVE = bpy.data.objects["Valve_0"]
def valve_pos(f):
    sc.frame_set(f); return VALVE.matrix_world.translation.copy()
# beat 1: crouched inside the ring at the fill valve, nozzle in both hands, rising as the tube swells; then stands, wipes brow
BEAT1R = {}
K = Vector((-5.3, -8.25, 0)); hose_pts = bpy.data.objects["Hose"].data.splines[0].points
for f in range(1, F(2.5) + 1, 4):
    v = valve_pos(f); u = (f - 1) / (F(2.5) - 1)
    ur = smooth((f - 60) / 26.0)                      # rises with the valve as the tube swells under it
    cr = 0.64 - 0.38 * ur + 0.015 * math.sin(f * 0.11)
    look = max(0.0, math.sin(f * 0.105)) ** 3          # glances up along the swelling tube about once a second
    stand(H, f, K, 0, flex=46 - 22 * ur, crouch=cr, head=(18 - 6 * smooth(u) - 30 * look, 12 * math.sin(f * 0.02) + 35 * look),
          feet={"L": Vector((K.x + 0.16, K.y + 0.02)), "R": Vector((K.x - 0.17, K.y + 0.12))})
    noz = v + Vector((0.0, 0.0, 0.21))                 # nozzle centre (stands upright on the valve cap)
    # right fist round the nozzle: palm on it from his side (+Y), fingers wrap toward +X, thumb opposed
    BEAT1R[f] = [noz + Vector((-0.07, 0.042, 0.0)), noz]
    H.key_hand("R", f, BEAT1R[f][0], Vector((1, 0, 0)), Vector((0, -1, 0)), pole=K + Vector((-0.7, 0.2, 0.5)))
    hose_mid = noz + Vector((0.24, 0.2, -0.12))
    dL = Vector((-0.7, -0.4, -0.6)).normalized()
    H.key_hand("L", f, hose_mid - dL * 0.085 + Vector((0, 0, 0.04)), dL, Vector((0.2, 0, -1)), pole=K + Vector((0.7, 0.2, 0.5)))
    # hose end tracks the valve and passes through the left hand
    hose_pts[-1].co = (*(noz + Vector((0, 0, 0.06))), 1.0); hose_pts[-1].keyframe_insert("co", frame=f)
    hose_pts[-2].co = (*(hose_mid + Vector((0.0, 0.0, -0.02))), 1.0); hose_pts[-2].keyframe_insert("co", frame=f)
    face(HR, f, brow=0.3, jaw=0.08, lids=0.2)

f0 = F(2.5)
for f, cr, fl_, mode in ((f0 + 10, 0.3, 26, "chest"), (f0 + 22, 0.16, 16, "chest"), (f0 + 34, 0.02, 4, "hang"), (f0 + 41, 0.0, 2, "up"), (f0 + 48, 0.0, 0, "brow"), (F(3.7), 0.0, 2, "brow")):
    stand(H, f, K + Vector((0, 0.12, 0)), -25 if f > f0 + 30 else -10, flex=fl_, crouch=cr, head=(-5, -35))
    arms(H, "Hero", f, K + Vector((0, 0.12, 0)), -25 if f > f0 + 30 else -10, mode)
grip(HR, "L", 1, 0.85); grip(HR, "L", F(2.5), 0.85); grip(HR, "L", F(2.5) + 12, 0.3)
grip(HR, "R", 1, 0.62); grip(HR, "R", F(8.3), 0.62); grip(HR, "R", F(8.5), 0.3)
face(HR, f0 + 40, brow=0.6, jaw=0.15, lids=0.4); face(HR, F(3.6), brow=0.2, jaw=0.0, lids=0.1, smile=0.6)
# beat 2: walks inside the ring along the front, checks each tube as it swells, hands on hips
p0 = K + Vector((0, 0.12, 0)); p1 = Vector((7.2, -7.4, 0))
path = lambda f: p0.lerp(p1, smooth((f - F(4.0)) / (F(6.6) - F(4.0))))
yaw_w = lambda f: -90 if F(4.1) < f < F(6.5) else -45
H.walk(path, yaw_w, F(4.0), F(6.6), stride=0.7)
for f in range(F(4.0), F(6.6) + 1, 4):
    ph = ((path(f) - p0).length / 0.7) % 1.0
    arms(H, "Hero", f, path(f), yaw_w(f), "hang", phase=ph, amp=0.6)
for f, yaw, mode, hd in ((F(6.8), -20, "hips", (10, 30)), (F(7.5), 10, "hips", (0, -10)), (F(8.2), 0, "hips", (-12, 0))):
    stand(H, f, p1, yaw, flex=4, head=hd); arms(H, "Hero", f, p1, yaw, mode)
face(HR, F(6.8), brow=0.0, smile=0.5); face(HR, F(8.2), brow=0.5, lids=0.3, jaw=0.1)
# beats 3-6: he heads up onto the porch (off camera) and watches from it
PORCH = Vector((2.3, -4.1, 0)); STEP = Vector((1.0, -5.6, 0))
pp = [p1, Vector((3.0, -6.6, 0)), STEP, PORCH]
def ppath(f):
    u = smooth((f - F(8.5)) / (F(11.5) - F(8.5))) * (len(pp) - 1); i = min(int(u), len(pp) - 2); return pp[i].lerp(pp[i + 1], u - i)
H.walk(ppath, lambda f: -30 + 30 * smooth((f - F(8.5)) / 120) + 180 * 0, F(8.5), F(11.5), stride=0.6)
for f in range(F(8.5), F(11.5) + 1, 4): arms(H, "Hero", f, ppath(f), -20, "hang", phase=f / 40, amp=0.5)
for f in range(F(11.6), F(21.3), 30):
    sway = math.sin(f * 0.03)
    stand(H, f, PORCH, 8 * sway, flex=3, side=2 * sway, head=(-4, 18 * sway)); arms(H, "Hero", f, PORCH, 8 * sway, "chest")
# beat 7: the slam: he flinches back, arms up, then stares
for f, dy, mode, fl_ in ((F(21.4), 0, "chest", 2), (F(21.6), 0.12, "up", -12), (F(22.0), 0.08, "up", -8), (F(22.8), 0.0, "hips", 6), (F(24.4), 0.0, "hips", 8)):
    stand(H, f, PORCH + Vector((0, dy, 0)), 0, flex=fl_, head=(-6 if fl_ < 0 else 6, 0)); arms(H, "Hero", f, PORCH + Vector((0, dy, 0)), 0, mode)
face(HR, F(21.4), brow=0.2); face(HR, F(21.6), brow=1.0, lids=1.0, jaw=0.5); face(HR, F(22.8), brow=0.7, lids=0.6, jaw=0.25)
# beat 10: amazed: steps to the porch edge, hands to head, brows up, jaw open
EDGE = PORCH + Vector((0.1, -0.2, 0))
for f, pos, mode, fl_, hd in ((F(28.2), PORCH, "hips", 6, (8, 0)), (F(28.7), EDGE, "hang", 2, (10, -20)), (F(28.95), EDGE, "up", -4, (0, -10)), (F(29.2), EDGE, "head", -6, (-8, 0)),
                              (F(29.9), EDGE, "head", -8, (-10, 15)), (F(30.3), EDGE, "out", 2, (5, -10))):
    stand(H, f, pos, 0, flex=fl_, head=hd); arms(H, "Hero", f, pos, 0, mode)
face(HR, F(28.2), brow=0.3, lids=0.3); face(HR, F(28.8), brow=1.0, lids=1.0, jaw=0.6); face(HR, F(29.9), brow=0.9, lids=0.8, jaw=0.3, smile=0.4)
face(HR, F(30.5), brow=0.6, lids=0.5, jaw=0.1, smile=0.9)
# beat 11: down the steps onto his dry lawn, arms out, looking around
LAWN = Vector((0.6, -7.2, 0)); dp = [EDGE, Vector((1.0, -4.9, 0)), STEP, LAWN]
def dpath(f):
    u = smooth((f - F(30.4)) / (F(31.8) - F(30.4))) * (len(dp) - 1); i = min(int(u), len(dp) - 2); return dp[i].lerp(dp[i + 1], u - i)
H.walk(dpath, lambda f: 0, F(30.4), F(31.8), stride=0.55)
for f in range(F(30.4), F(31.8) + 1, 4): arms(H, "Hero", f, dpath(f), 0, "hang", phase=f / 35, amp=0.4)
for f, yaw, hd in ((F(32.2), 20, (-10, 30)), (F(32.9), -25, (-14, -30)), (F(33.5), 0, (-15, 0))):
    stand(H, f, LAWN, yaw, flex=-4, head=hd); arms(H, "Hero", f, LAWN, yaw, "out")
face(HR, F(33.3), brow=0.5, lids=0.4, jaw=0.15, smile=1.0)

# NeighbourA (across the street): wheels her bin up the drive (beats 1-2), runs to her door (beat 3), watches (later)
NA = HU["NeighbourA"]; BIN = bpy.data.objects["bin"]
bins = []
for i, (x, y) in enumerate(((7.0, -21.6), (30.0, -12.4), (-14.0, -12.4), (24.5, -21.6), (-29.5, -12.5))):
    b = bpy.data.objects.new(f"Bin_{i}", BIN.data); sc.collection.objects.link(b); b.location = (x, y, -0.02); bins.append(b)
pa0, pa1 = Vector((7.6, -21.0, 0)), Vector((7.6, -27.4, 0))
pathA = lambda f: pa0.lerp(pa1, (f - F(0.3)) / (F(7.5) - F(0.3)))
NA.walk(pathA, lambda f: 180, F(0.3), F(7.5), stride=0.6)
b0 = bins[0]
for f in range(F(0.3), F(7.5) + 1, 4):
    p = pathA(f); arms(NA, "NeighbourA", f, p, 180, "hang")
    # bin tilted back on its wheels, handle in her hands
    b0.location = (p.x, p.y - 0.75, ground_z(p.x, p.y - 0.75) + 0.0); b0.rotation_euler = (R_(-24), 0, R_(180)); b0.keyframe_insert("location", frame=f); b0.keyframe_insert("rotation_euler", frame=f)
    W = b0.matrix_world @ Vector((0, 0.38, 1.0)) if False else Vector((p.x, p.y - 0.42, 0.98))
    for s, dx in (("L", 0.17), ("R", -0.17)):
        NA.key_hand(s, f, W + Vector((-dx, 0, 0)), Vector((0, 1, -0.6)), Vector((0, 0, -1)), pole=p + Vector((dx * 3, 0.4, 1.0)))
for s_ in "LR": grip(RIG["NeighbourA"], s_, F(0.3), 0.8); grip(RIG["NeighbourA"], s_, F(7.5), 0.8); grip(RIG["NeighbourA"], s_, F(7.8), 0.25)
for f in (F(7.8), F(8.2)): arms(NA, "NeighbourA", f, pa1, 180, "hang")
pa2 = Vector((3.2, -31.6, 0))
NA.walk(lambda f: pa1.lerp(pa2, smooth((f - F(8.4)) / (F(10.2) - F(8.4)))), lambda f: 200, F(8.4), F(10.2), stride=1.1, lift=0.14, lean=14)
for f in range(F(8.4), F(10.2) + 1, 4): arms(NA, "NeighbourA", f, pa1.lerp(pa2, smooth((f - F(8.4)) / (F(10.2) - F(8.4)))), 200, "hang", phase=f / 25, amp=0.55)
arms(NA, "NeighbourA", F(10.25), pa2, 200, "chest")
for f in range(F(10.4), 2011, 60):
    s_ = math.sin(f * 0.02); stand(NA, f, pa2, 190 + 10 * s_, head=(0, 25 * s_)); arms(NA, "NeighbourA", f, pa2, 190 + 10 * s_, "hips" if (f // 60) % 2 else "chest")
face(RIG["NeighbourA"], F(8.4), brow=1.0, lids=0.9, jaw=0.5)

# NeighbourB (left neighbour, north row): looks at the sky, carries on, then backs away from the water (beat 4), and his wrecked lawn (beat 9)
NB = HU["NeighbourB"]
pb0 = Vector((-15.0, -7.0, 0)); pb1 = Vector((-20.5, -4.6, 0))
for f, hd, md in ((1, (-25, 10), "hips"), (F(1.4), (-30, -15), "hips"), (F(2.6), (-10, 0), "hang")):
    stand(NB, f, pb0, 30, head=hd); arms(NB, "NeighbourB", f, pb0, 30, md)
NB.walk(lambda f: pb0.lerp(pb1, smooth((f - F(2.8)) / (F(6.0) - F(2.8)))), lambda f: 120, F(2.8), F(6.0), stride=0.65)
for f in range(F(2.8), F(6.0) + 1, 4): arms(NB, "NeighbourB", f, pb0.lerp(pb1, smooth((f - F(2.8)) / (F(6.0) - F(2.8)))), 120, "hang", phase=f / 40, amp=0.5)
bpath = lambda f: pb1.lerp(pb1 + Vector((0, 1.1, 0)), smooth((f - F(11.8)) / (F(13.4) - F(11.8))))
stand(NB, F(11.6), pb1, 0, flex=-6, head=(10, 0)); arms(NB, "NeighbourB", F(11.6), pb1, 0, "hang")
NB.walk(bpath, lambda f: 0, F(11.8), F(13.4), stride=0.45, lean=-6)
for f, mode in ((F(12.2), "up"), (F(12.9), "up"), (F(13.4), "chest")): arms(NB, "NeighbourB", f, bpath(f), 0, mode)
for f, mode in ((F(13.6), "chest"), (F(14.6), "hips")):
    stand(NB, f, pb1 + Vector((0, 1.1, 0)), 0, flex=-6, head=(10, 0)); arms(NB, "NeighbourB", f, pb1 + Vector((0, 1.1, 0)), 0, mode)
face(RIG["NeighbourB"], F(11.8), brow=1.0, lids=1.0, jaw=0.7)
pb2 = Vector((-23.6, -8.0, 0))
pbm = pb1 + Vector((0, 1.1, 0))
for f, md in ((F(16.0), "hips"), (F(20.0), "hips"), (F(23.9), "hips"), (F(24.4), "hang")):
    stand(NB, f, pbm, 0, flex=-2, head=(5, 0)); arms(NB, "NeighbourB", f, pbm, 0, md)
wpath = lambda f: pbm.lerp(pb2, smooth((f - F(24.5)) / (F(26.1) - F(24.5))))
NB.walk(wpath, lambda f: -35, F(24.5), F(26.1), stride=0.7)
for f in range(F(24.5), F(26.1) + 1, 4): arms(NB, "NeighbourB", f, wpath(f), -35, "hang", phase=f / 40, amp=0.4)
for f, yaw, mode, hd in ((F(26.2), 60, "hips", (15, 0)), (F(26.55), 45, "chest", (18, 10)), (F(26.9), 30, "chest", (20, 20)), (F(27.25), 55, "chest", (15, 0)), (F(27.6), 80, "hips", (10, -25)), (F(28.4), 40, "hang", (25, 0))):
    stand(NB, f, pb2, yaw, flex=12, head=hd); arms(NB, "NeighbourB", f, pb2, yaw, mode)
face(RIG["NeighbourB"], F(26.2), brow=-0.6, lids=-0.3, jaw=0.1); face(RIG["NeighbourB"], F(27.6), brow=-0.8, jaw=0.25)

# ------------------------------------------------------------------ debris: floating car, bins, fence panels, sofa
car = bpy.data.objects.new("FloatCar", bpy.data.objects["car"].data); sc.collection.objects.link(car)
car.location = (58, -13.4, -0.12); car.rotation_euler = (0, 0, R_(90))
lift = F(8.9)
car.keyframe_insert("location", frame=1); car.keyframe_insert("rotation_euler", frame=1); car.keyframe_insert("location", frame=lift); car.keyframe_insert("rotation_euler", frame=lift)
for f in range(lift + 10, F(24.5), 10):
    u = (f - lift) / (F(24.5) - lift)
    x = 58 - 74 * (1 - (1 - u) ** 1.6)
    lv = level_at(f)
    car.location = (x, -16.0 + 1.6 * math.sin(u * 5), lv - 0.72 + 0.05 * math.sin(f * 0.13))
    car.rotation_euler = (R_(4 * math.sin(f * 0.07)), R_(6 * math.sin(f * 0.05)), R_(90 + 140 * u))
    car.keyframe_insert("location", frame=f); car.keyframe_insert("rotation_euler", frame=f)
car.location = (-16.5, -14.6, -0.12); car.rotation_euler = (R_(3), R_(-4), R_(90 + 150)); car.keyframe_insert("location", frame=F(26.0)); car.keyframe_insert("rotation_euler", frame=F(26.0))
for i, b in enumerate(bins[1:]):
    x0 = b.location.x; lf = None
    for f in range(F(8.3), F(24.5), 8):
        fx = front_at(f)
        if lf is None and fx < x0 + 2: lf = f; b.keyframe_insert("location", frame=f); b.keyframe_insert("rotation_euler", frame=f)
        if lf is None: continue
        u = (f - lf) / 60.0
        lv = level_at(f)
        b.location = (x0 - 4.0 * u - 0.4 * i, b.location.y + 0.0, max(-0.12, lv - 0.5) + 0.04 * math.sin(f * 0.2 + i))
        b.rotation_euler = (R_(80 + 10 * math.sin(f * 0.09 + i)), R_(20 * math.sin(f * 0.05)), R_(30 * u + 40 * i))
        b.keyframe_insert("location", frame=f); b.keyframe_insert("rotation_euler", frame=f)
    b.location = (b.location.x, b.location.y + 1.0, -0.02 + 0.33); b.rotation_euler = (R_(88), 0, R_(25 * i)); b.keyframe_insert("location", frame=F(26.0)); b.keyframe_insert("rotation_euler", frame=F(26.0))
FENCE = bpy.data.objects["fence"]
for i in range(3):
    fo = bpy.data.objects.new(f"Fence_{i}", FENCE.data); sc.collection.objects.link(fo)
    fo.location = (-11.6, -9.8 + 3.08 * i + 1.54, 0); fo.keyframe_insert("rotation_euler", frame=1)
    t0 = F(12.0) + 9 * i
    fo.keyframe_insert("rotation_euler", frame=t0)
    fo.rotation_euler = (0, R_(-14), 0); fo.keyframe_insert("rotation_euler", frame=t0 + 12)
    fo.rotation_euler = (0, R_(-84), 0); fo.keyframe_insert("rotation_euler", frame=t0 + 34)
    fo.rotation_euler = (R_(4), R_(-80), R_(-6)); fo.keyframe_insert("rotation_euler", frame=t0 + 70)
    fo.keyframe_insert("location", frame=t0 + 34); fo.location.z = 0.42; fo.location.x -= 0.4; fo.keyframe_insert("location", frame=t0 + 90)
    fo.location.z = 0.05; fo.keyframe_insert("location", frame=F(26.0))
sofa = bpy.data.objects.new("WetSofa", bpy.data.objects["sofa"].data); sc.collection.objects.link(sofa)
sofa.location = (-21.8, -7.6, 0.0); sofa.rotation_euler = (R_(3), R_(-2), R_(18)); khide(sofa, [(F(24.4), 2011)])
sofa2 = bpy.data.objects.new("WetSofa2", bpy.data.objects["sofa"].data); sc.collection.objects.link(sofa2)
sofa2.location = (22.5, -7.2, 0.0); sofa2.rotation_euler = (0, 0, R_(-30)); khide(sofa2, [(F(24.4), 2011)])
# wind sway on trees
for t in [o for o in bpy.data.objects if o.name.startswith("Tree_")]:
    ph = random.uniform(0, 6)
    for f in range(1, 2011, 40):
        wnd = 1.0 if f < F(25) else 0.3
        t.rotation_euler.x = R_(2.5 * wnd * math.sin(f * 0.09 + ph)); t.rotation_euler.y = R_(1.8 * wnd * math.sin(f * 0.07 + ph * 2))
        t.keyframe_insert("rotation_euler", frame=f)

def grip_ring(rig, s):
    """centre and axis of the space enclosed by the curled fingers (where a held cylinder sits)"""
    P = rig.pose.bones; M = rig.matrix_world
    pts = []
    for fi in range(2, 6):
        pts.append(M @ P[f"finger{fi}-1.{s}"].head); pts.append(M @ P[f"finger{fi}-2.{s}"].tail)
    c = sum(pts, Vector()) / len(pts)
    ax = (M @ P[f"finger2-1.{s}"].head) - (M @ P[f"finger5-1.{s}"].head)
    return c, ax.normalized()
# beat 1: move the right-hand IK target until the finger ring sits on the nozzle (real contact, no gap)
for it in range(3):
    worst = 0.0
    for f, (W, noz) in sorted(BEAT1R.items()):
        sc.frame_set(f); c, ax = grip_ring(HR, "R"); e = noz - c
        wr = HR.matrix_world @ HR.pose.bones["wrist.R"].head; tg = HR.matrix_world @ HR.pose.bones["IK_hand.R"].head
        if (wr - tg).length > 0.015:        # out of reach: pull the target back toward the wrist instead of pushing further
            e = (wr - tg) * 0.8
        else:
            worst = max(worst, e.length)
        if e.length > 0.08: e = e.normalized() * 0.08
        BEAT1R[f][0] = W + e
        H.key_hand("R", f, BEAT1R[f][0], Vector((1, 0, 0)), Vector((0, -1, 0)), pole=K + Vector((-0.7, 0.2, 0.5)))
    print("GRIP_SOLVE iter", it, "worst gap %.3f m" % worst)
    if it == 2:
        for f, (W, noz) in sorted(BEAT1R.items()):
            sc.frame_set(f); c, ax = grip_ring(HR, "R"); wr = HR.matrix_world @ HR.pose.bones["wrist.R"].head
            tg = HR.matrix_world @ HR.pose.bones["IK_hand.R"].head
            print("GAP", f, round((noz - c).length, 3), "wrist-target", round((wr - tg).length, 3))
# the nozzle comes off the valve at 2.5 s and stays in his right fist while he walks the ring (hose trailing)
NOZ = bpy.data.objects["Nozzle"]; cnz = NOZ.constraints[0]
cnz.influence = 0.0          # the nozzle sits in his fist's finger ring from the first frame (pressed onto the valve in beat 1)
for f in range(1, F(8.4), 2):
    sc.frame_set(f)
    p, x = grip_ring(HR, "R")
    if f <= F(2.5):
        # seated on the valve: the nozzle runs from the valve cap up through his fist (never floating, never off the hand)
        top = VALVE.matrix_world.translation + Vector((0, 0, 0.15))
        ax = (p - top); ln = max(0.05, ax.length); x = ax.normalized()
        NOZ.location = top + x * (ln / 2 + 0.02); NOZ.scale = (1, 1, (ln + 0.04) / 0.12)
    else:
        NOZ.location = p; NOZ.scale = (1, 1, 1)
    NOZ.keyframe_insert("location", frame=f); NOZ.keyframe_insert("scale", frame=f)
    NOZ.rotation_euler = x.to_track_quat("Z", "Y").to_euler(); NOZ.keyframe_insert("rotation_euler", frame=f)
    tip = NOZ.location + x * (0.06 * NOZ.scale.z)
    hose_pts[-1].co = (*(tip), 1.0); hose_pts[-1].keyframe_insert("co", frame=f)
    hose_pts[-2].co = (*(Vector((p.x + 0.25, p.y + 0.5, 0.03))), 1.0); hose_pts[-2].keyframe_insert("co", frame=f)
    hose_pts[-3].co = (*(Vector(((p.x + hose_pts[1].co[0]) / 2, (p.y + hose_pts[1].co[1]) / 2, 0.02))), 1.0); hose_pts[-3].keyframe_insert("co", frame=f)
# hide the library source objects
for n in ("house_a", "house_b", "house_c", "house_d", "house_e", "hero_house", "car", "bin", "fence", "sofa", "hose"):
    o = bpy.data.objects.get(n)
    if o and o.users_collection: o.hide_render = True; o.hide_viewport = True

# ------------------------------------------------------------------ the one camera
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.sensor_width = 36; cam.data.clip_start = 0.02; cam.data.clip_end = 400
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 4.0
V = Vector
CAM = [  # (t seconds, position, look-at, lens)
    (0.0, V((-1.4, -9.7, 0.62)), V((-5.0, -8.5, 0.45)), 24),
    (1.0, V((-4.0, -10.2, 2.0)), V((-5.3, -8.4, 0.6)), 30),
    (2.0, V((-4.6, -11.3, 2.35)), V((-5.3, -8.6, 0.6)), 30),
    (3.0, V((-7.9, -10.4, 1.45)), V((-4.4, -8.8, 0.55)), 28),
    (3.7, V((-8.6, -12.3, 2.6)), V((-3.0, -8.6, 0.5)), 24),
    (4.7, V((-6.0, -17.0, 6.0)), V((0.0, -6.5, 0.5)), 22),
    (5.7, V((7.5, -20.0, 10.5)), V((0.5, -1.0, 0.0)), 22),
    (6.7, V((16.0, -9.0, 12.5)), V((0.0, 1.0, 0.0)), 22),
    (7.8, V((14.0, 4.0, 11.0)), V((0.0, 0.0, 0.0)), 22),
    (8.5, V((9.0, -9.5, 5.0)), V((38.0, -16.0, 0.3)), 20),
    (9.5, V((12.5, -14.0, 1.7)), V((34.0, -16.0, 0.4)), 22),
    (10.5, V((6.5, -11.2, 2.7)), V((18.0, -16.0, 0.4)), 20),
    (11.5, V((-3.0, -11.0, 2.5)), V((5.0, -16.0, 0.4)), 22),
    (12.3, V((-13.5, -12.0, 1.5)), V((-21.5, -3.6, 0.9)), 24),
    (13.3, V((-15.0, -10.6, 1.3)), V((-11.0, -6.0, 0.6)), 26),
    (14.0, V((-6.5, -14.0, 2.2)), V((1.5, -9.0, 0.4)), 24),
    (14.6, V((3.4, -10.9, 0.75)), V((2.0, -9.0, 0.45)), 30),
    (15.0, V((3.0, -9.95, 0.55)), V((2.0, -9.0, 0.45)), 30),
    (15.5, V((4.3, -9.55, 0.6)), V((1.8, -9.0, 0.4)), 28),
    (16.4, V((3.9, -10.4, 0.95)), V((2.0, -9.0, 0.4)), 30),
    (17.2, V((3.7, -10.0, 0.25)), V((2.0, -9.0, 0.28)), 30),
    (18.2, V((4.8, -9.3, 0.7)), V((2.0, -9.6, 0.5)), 24),
    (19.2, V((4.3, -11.0, 0.75)), V((2.0, -9.4, 0.6)), 24),
    (20.2, V((3.6, -9.7, 0.2)), V((2.1, -9.0, 1.0)), 22),
    (21.0, V((3.4, -6.0, 3.0)), V((2.8, -14.0, 0.2)), 22),
    (21.4, V((3.0, -5.6, 2.9)), V((3.0, -16.0, 0.2)), 22),
    (22.4, V((8.5, -5.5, 3.3)), V((12.5, -14.0, 0.2)), 22),
    (23.5, V((14.0, -18.5, 9.0)), V((0.0, 0.0, 0.0)), 20),
    (24.5, V((-4.0, -24.0, 6.0)), V((-3.0, -16.0, 0.0)), 22),
    (25.6, V((-12.5, -15.5, 1.0)), V((-18.0, -12.5, 0.2)), 24),
    (26.4, V((-13.0, -14.0, 2.2)), V((-21.5, -5.0, 0.8)), 24),
    (27.5, V((-28.0, -15.0, 2.4)), V((-22.0, -6.5, 0.6)), 24),
    (28.2, V((-10.0, -11.5, 1.6)), V((-2.0, -6.0, 1.2)), 24),
    (29.2, V((0.6, -8.4, 2.4)), V((2.4, -4.3, 2.6)), 30),
    (30.3, V((3.4, -7.1, 2.7)), V((2.4, -4.3, 2.75)), 38),
    (31.3, V((1.8, -5.6, 3.4)), V((0.6, -7.8, 0.9)), 26),
    (32.3, V((1.0, -10.0, 16.0)), V((0.4, -2.0, 0.0)), 28),
    (33.5, V((0.5, -3.5, 42.0)), V((0.2, -0.8, 0.0)), 28),
]
keys_p = [(F(t), p) for t, p, q, l in CAM]; keys_q = [(F(t), q) for t, p, q, l in CAM]; keys_l = [(F(t), float(l)) for t, p, q, l in CAM]
cp, cq, cl = catmull(keys_p), catmull(keys_q), pchip(keys_l)
prev = None
for f in range(1, 2011, 2):
    p = cp(f); q = cq(f)
    # tiny handheld drift
    p = p + Vector((0.012 * math.sin(f * 0.031), 0.01 * math.sin(f * 0.023 + 1), 0.008 * math.sin(f * 0.041 + 2)))
    rot = (q - p).to_track_quat("-Z", "Y")
    if prev is not None and rot.dot(prev) < 0: rot = -rot
    prev = rot
    cam.location = p; cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = rot
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_quaternion", frame=f)
    cam.data.lens = cl(f); cam.data.keyframe_insert("lens", frame=f)
    cam.data.dof.focus_distance = max(0.3, (q - p).length); cam.data.dof.keyframe_insert("focus_distance", frame=f)
# bubbles drift up through the section, silt swirls (life inside the cutaway)
for o in [o for o in bpy.data.objects if o.name.startswith("Bubble_")]:
    z0 = o.location.z; ph = random.uniform(0, 6)
    for f in range(CUT_IN, CUT_OUT + 1, 30):
        u = (f - CUT_IN) / 60.0
        o.location.z = min(0.76, z0 + 0.025 * u); o.location.y += 0.0; o.keyframe_insert("location", index=2, frame=f)
for o in [o for o in bpy.data.objects if o.name.startswith("Silt_")]:
    p0 = o.location.copy(); ph = random.uniform(0, 6)
    for f in range(F(17.0), CUT_OUT + 1, 30):
        o.location = p0 + Vector((0.08 * math.sin(f * 0.02 + ph), 0.05 * math.sin(f * 0.03 + ph), 0.03 * math.sin(f * 0.025 + ph)))
        o.keyframe_insert("location", frame=f)
sc["beats"] = str([F(t) for t in (0.0, 3.7, 8.3, 11.8, 13.6, 17.2, 21.4, 24.5, 26.4, 28.2, 30.3)])
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
