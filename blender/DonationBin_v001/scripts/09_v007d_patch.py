"""DonationBin v007d patch, applied to the packed v007c file (director review of 7677a55).
blender -b DonationBin_v007c_60fps.blend --python 09_v007d_patch.py -- out.blend
Camera: the flagged ranges are re-shot as simple, steady shots joined by HARD CUTS (no whip-pans, no camera
passing through or brushing anything). Inside the bin the camera sits at her eye level on the face side,
tracks her (smoothed) face, and cuts about every 2 s between two angles. A soft fill light rides with the camera
inside the bin so her face reads (no black-hole face).
Acting: the frozen holds get small moves (head turns, breathing), the stiff side arm at 511-596 rests on the
clothes, the wall-bang alternates real pushes, and the hand that rests on the wall at 676-916 slides along it."""
import sys, json, math
import bpy
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
exec(open("/home/user/Muhammed/blender/pipeline/hand_poses.py").read())
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; cam = sc.camera; cd = cam.data
FE = sc.frame_end
WO = bpy.data.objects["Woman"]
WMESH = set(c.name for c in WO.children_recursive)
def dg(): return bpy.context.evaluated_depsgraph_get()
def headpos(r, f):
    sc.frame_set(f); hb = r.pose.bones["head"]; M = r.matrix_world
    hd = M @ hb.head; up = (M @ hb.tail - hd).normalized()
    fwl = r.data.bones["head"].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0))
    fw = (M.to_3x3() @ (hb.matrix.to_3x3() @ fwl)).normalized()
    return hd + up * 0.06 + fw * 0.05, fw
def ray(o, d, L=5.0):
    h = sc.ray_cast(dg(), Vector(o), Vector(d).normalized(), distance=L)
    return h if h[0] else None
def air(c, r=0.15):
    for d in (Vector((1, 0, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((0, 0, -1)),
              Vector((1, 1, 0)), Vector((-1, 1, 0)), Vector((1, -1, 0)), Vector((-1, -1, 0))):
        if ray(c, d, r): return False
    return True
def sees(c, p, own=WMESH):
    v = p - c; h = ray(c, v, v.length)
    return h is None or (h[1] - c).length > v.length - 0.10 or h[4].name in own

# ---------------------------------------------------------------- current camera, per frame
sc.frame_set(1)
CUR = {}
for f in range(1, FE + 1):
    sc.frame_set(f)
    CUR[f] = [cam.matrix_world.translation.copy(), cam.matrix_world.to_quaternion(), cd.lens]
NEW = {}
INSIDE = dict(x=(-0.60, 0.60), y=(-0.45, 0.46), z=(0.35, 2.20))
def inbox(c, B):
    return B["x"][0] < c.x < B["x"][1] and B["y"][0] < c.y < B["y"][1] and B["z"][0] < c.z < B["z"][1]
def smooth_face(r, f0, f1, k=12):
    raw = {f: headpos(r, f)[0] for f in range(f0 - k, f1 + k + 1)}
    return {f: sum((raw[g] for g in range(f - k, f + k + 1)), Vector()) / (2 * k + 1) for f in range(f0, f1 + 1)}
def face_shot(f0, f1, angs, dists, ups=(0.0, -0.06, 0.08, 0.16, 0.25), lens=24, B=INSIDE, push=0.0, r=WO, aim=Vector((0, 0, -0.04)), name=""):
    """fixed camera on her face side at eye level; tracks the smoothed face; optional slow push-in"""
    fm, fw = headpos(r, (f0 + f1) // 2)
    fh = Vector((fw.x, fw.y, 0)); fh = fh.normalized() if fh.length > 0.2 else Vector((0, -1, 0))
    tr = smooth_face(r, f0, f1)
    own = set(c.name for c in r.children_recursive)
    for d in dists:
        for a in angs:
            for u in ups:
                c = fm + (Matrix.Rotation(math.radians(a), 3, 'Z') @ fh) * d + Vector((0, 0, u))
                if not inbox(c, B): continue
                sc.frame_set(f0)
                if not air(c): continue
                ok = True
                for g in (f0, (f0 + f1) // 2, f1, f0 + (f1 - f0) // 4, f0 + 3 * (f1 - f0) // 4):
                    p_, _ = headpos(r, g)
                    if not sees(c, p_, own) or (p_ - c).length < 0.38: ok = False; break
                if not ok: continue
                for f in range(f0, f1 + 1):
                    t = (f - f0) / max(1, f1 - f0)
                    cc = c + (tr[f] - c).normalized() * push * t
                    NEW[f] = [cc, (tr[f] + aim - cc).to_track_quat('-Z', 'Y'), lens]
                print("SHOT", name, f0, f1, "a", a, "d", d, "u", u, "cam", tuple(round(x, 2) for x in c))
                return True
    print("NOSHOT", name, f0, f1)
    return False
def fixed_shot(f0, f1, c0, t0, c1=None, t1=None, lens=24, track=None, name=""):
    c0, t0 = Vector(c0), Vector(t0); c1 = Vector(c1) if c1 else c0; t1 = Vector(t1) if t1 else t0
    for f in range(f0, f1 + 1):
        u = (f - f0) / max(1, f1 - f0); u = u * u * (3 - 2 * u)
        c = c0.lerp(c1, u); t = t0.lerp(t1, u)
        if track: t = track(f)
        NEW[f] = [c, (t - c).to_track_quat('-Z', 'Y'), lens]
    print("FIXED", name, f0, f1)
def group_track(rigs, f0, f1, k=15, dz=-0.10):
    raw = {}
    for f in range(f0 - k, f1 + k + 1):
        raw[f] = sum((headpos(bpy.data.objects[n], f)[0] for n in rigs), Vector()) / len(rigs)
    sm = {f: sum((raw[g] for g in range(f - k, f + k + 1)), Vector()) / (2 * k + 1) + Vector((0, 0, dz)) for f in range(f0, f1 + 1)}
    return lambda f: sm[f]

A1 = (30, -30, 40, -40, 20, -20, 50, -50, 60, -60, 10, -10, 70, -70)
A2 = (-30, 30, -40, 40, -20, 20, -50, 50, -60, 60, -10, 10, -70, 70)
D_IN = (0.62, 0.56, 0.50, 0.45, 0.40)
# 5. 286-296: her jeans filled the frame mid-fall -> cut at 281 to a high inside corner wide of her landing
fixed_shot(281, 330, (-0.55, 0.42, 2.05), (-0.20, -0.10, 0.70), lens=16, name="landing wide")
# 3. 331-504: eye level on her face (two angles, cut ~2 s)
face_shot(331, 420, A1, D_IN, lens=24, name="sit A")
face_shot(421, 504, A2, D_IN, lens=24, name="sit B")
# 6. 505-600: sitting (arm fixed below) - two angles
face_shot(505, 552, A1, D_IN, lens=24, name="explain A")
face_shot(553, 600, A2, D_IN, lens=24, name="explain B")
# 5. 601-675: she gets up - face side, wider
face_shot(601, 675, A1, (0.62, 0.56, 0.50), ups=(0.0, -0.10, 0.10, -0.20), lens=18, name="stands")
# 4. 676-916: face fully in frame, cut ~2 s
face_shot(676, 795, A1, D_IN, lens=22, push=0.05, name="walls A")
face_shot(796, 916, A2, D_IN, lens=22, push=0.05, name="walls B")
# 5. 917-960 (hair filled the frame)
face_shot(917, 960, A1, D_IN, lens=22, name="beat6 lead")
# 7. 1201-1291 wall-bang: cut at 1246 to a second angle
face_shot(1181, 1245, A2, D_IN, ups=(0.0, -0.10, -0.20, -0.30), lens=18, name="bang A")
face_shot(1246, 1300, A1, D_IN, ups=(0.0, -0.10, -0.20, -0.30), lens=18, name="bang B")
# 1. 1301-1320: (camera was inside her torso)
face_shot(1301, 1320, A2, D_IN, lens=22, name="pre-scream")
# 1./8. 1395-1470: end the scream shot, hard cut to a short exterior push-in, then cut back inside (beat 8)
for f in range(1395, 1401): NEW[f] = CUR[1394]
fixed_shot(1401, 1470, (0.45, -3.10, 1.85), (0.0, -0.6, 1.30), (0.30, -2.30, 1.65), (0.0, -0.6, 1.30), lens=24, name="exterior")
# 2. 1471-1860: three days, eye level on her face, cut between two angles every ~2 s (+ fill light)
cuts = [1471, 1561, 1671, 1771, 1861]
for i, (a_, b_) in enumerate(zip(cuts, cuts[1:])):
    face_shot(a_, b_ - 1, A1 if i % 2 == 0 else A2, (0.62, 0.55, 0.48, 0.42), ups=(0.0, 0.08, 0.16, 0.25, 0.35, -0.05), lens=24, push=0.04, name="days%d" % i)
# 1. 1861-1879: hard cut straight onto the passer-by shot (no black, no sky)
for f in range(1861, 1880): NEW[f] = CUR[1880]
# 5. 1936-2075: wide exterior on the knock and the rescue (no head/arm/back filling the lens)
PB = bpy.data.objects["Passerby"]
fixed_shot(1936, 1985, (1.75, -2.60, 1.55), (0.45, -0.85, 1.35), lens=26, name="knock wide")
fixed_shot(1986, 2030, (0.10, -3.20, 1.70), (0.10, -0.75, 1.05), lens=22, name="cutting wide")
fixed_shot(2031, 2075, (1.90, -2.70, 1.50), (0.30, -0.80, 0.95), lens=24, name="cutting angle2")
# 1. 2076-2095: inside on her face as the light comes in
face_shot(2076, 2095, A1, D_IN, lens=22, name="light")
# 5. 2096-2125: outside, low, facing her as she crawls out (not the back of her head)
fixed_shot(2096, 2125, (0.35, -1.75, 0.75), (0.0, -0.4, 0.70), lens=24, track=None, name="crawl front")
_tr = smooth_face(WO, 2096, 2125)
for f in range(2096, 2126):
    c = NEW[f][0]; NEW[f] = [c, (_tr[f] + Vector((0, 0, -0.10)) - c).to_track_quat('-Z', 'Y'), 24]
# 9. 2341-2490: end closer on her with the firefighters (faces), slow push-in
gt = group_track(["Woman", "FireB"], 2341, FE)
m0 = gt(2341); fwW = headpos(WO, 2400)[1]; fh = Vector((fwW.x, fwW.y, 0)).normalized()
c0 = m0 + fh * 2.4 + Vector((0, 0, 0.05)); c1 = m0 + fh * 1.7 + Vector((0, 0, 0.05))
fixed_shot(2341, FE, c0, m0, c1, m0, lens=28, track=gt, name="ending")

# ---------------------------------------------------------------- bake: every frame keyed, constant (hard cuts)
for f, v in NEW.items(): CUR[f] = v
def fcs(idb):
    ad = idb.animation_data
    return [c for l in ad.action.layers for st in l.strips for cb in st.channelbags for c in cb.fcurves] if ad and ad.action else []
for c in fcs(cam) + fcs(cd): c.keyframe_points.clear()
cam.rotation_mode = 'QUATERNION'; qp = None
for f in range(1, FE + 1):
    p, q, ln = CUR[f]; q = q.copy()
    if qp is not None and q.dot(qp) < 0: q = -q
    qp = q
    cam.location = p; cam.keyframe_insert("location", frame=f)
    cam.rotation_quaternion = q; cam.keyframe_insert("rotation_quaternion", frame=f)
    cd.lens = ln; cd.keyframe_insert("lens", frame=f)
for c in fcs(cam) + fcs(cd):
    if c.data_path.startswith("dof"): continue
    for kp in c.keyframe_points: kp.interpolation = 'LINEAR'
cd.dof.use_dof = False          # readable faces: no shallow focus on the review cuts
print("CAM_REBAKED", len(NEW))

# ---------------------------------------------------------------- fill light riding with the camera (inside the bin)
fl = bpy.data.lights.new("CamFill", 'AREA'); fl.size = 0.35; fl.color = (1.0, 0.92, 0.82)
flo = bpy.data.objects.new("CamFill", fl); sc.collection.objects.link(flo)
flo.parent = cam; flo.location = (0.0, 0.12, 0.0)          # just above the lens, facing the same way
flo.visible_camera = False
def fill(f, e):
    fl.energy = e; fl.keyframe_insert("energy", frame=f)
for f, e in ((1, 0), (280, 0), (281, 6), (1394, 6), (1395, 0), (1470, 0), (1471, 10), (1860, 10), (1861, 0), (2075, 0), (2076, 6), (2095, 6), (2096, 0)):
    fill(f, e)
for c in fcs(fl):
    for kp in c.keyframe_points: kp.interpolation = 'CONSTANT'
print("FILL_LIGHT")

# ---------------------------------------------------------------- acting
def key_rot_delta(r, bn, f, ax, deg):
    sc.frame_set(f); pb = r.pose.bones[bn]
    pb.rotation_mode = 'QUATERNION'
    pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion(ax, math.radians(deg))
    pb.keyframe_insert("rotation_quaternion", frame=f, group=bn)
def anchor(r, bn, fs):
    for f in fs:
        sc.frame_set(f); pb = r.pose.bones[bn]; pb.keyframe_insert("rotation_quaternion", frame=f, group=bn)
        if bn.startswith("IK"): pb.keyframe_insert("location", frame=f, group=bn)
# breathing and small head moves on the frozen holds
HOLDS = [(511, 600), (676, 916), (1201, 1291), (1471, 1860)]
for a_, b_ in HOLDS:
    anchor(WO, "head", (a_ - 2, b_ + 2)); anchor(WO, "spine03", (a_ - 2, b_ + 2))
    vals = {}
    for i, f in enumerate(range(a_ + 20, b_ - 10, 40)):
        vals[f] = (8 * math.sin(i * 1.7), 4 * math.sin(i * 2.3 + 1.0), 2.0 * (1 if i % 2 else -1))
    for f, (yaw, pitch, br) in vals.items():
        key_rot_delta(WO, "head", f, Vector((0, 1, 0)), yaw)
        key_rot_delta(WO, "head", f, Vector((1, 0, 0)), pitch)
        key_rot_delta(WO, "spine03", f, Vector((1, 0, 0)), br)
print("HOLD_MOVES")
# 6. 511-596: the arm stuck straight out to the side rests on the clothes beside her hip
CLOTH = [bpy.data.objects[n] for n in sc["pile_colliders"].split(",")]
def cloth_z(x, y):
    z = None
    for o in CLOTH:
        inv = o.matrix_world.inverted()
        h, loc, n, i = o.ray_cast(inv @ Vector((x, y, 3.0)), (inv.to_3x3() @ Vector((0, 0, -1))).normalized())
        if h:
            wz = (o.matrix_world @ loc).z; z = wz if z is None else max(z, wz)
    return z
def W(b, tail=False):
    pb = WO.pose.bones[b]; return WO.matrix_world @ (pb.tail if tail else pb.head)
sc.frame_set(555)
side = max("LR", key=lambda s: (W("wrist." + s) - W("spine03")).length)
print("STIFF_ARM", side, round((W("wrist." + side) - W("spine03")).length, 2))
names = ["IK_hand." + side] + _chain(side)
for g in (499, 606):
    sc.frame_set(g)
    for n in names:
        pb = WO.pose.bones[n]
        if n.startswith("IK"): pb.keyframe_insert("location", frame=g, group=n)
        pb.keyframe_insert("rotation_quaternion", frame=g, group=n)
for f in range(505, 601, 8):
    sc.frame_set(f)
    sh = W("upperarm01." + side); hp = W("spine05")
    out = Vector((sh.x - hp.x, sh.y - hp.y, 0)); out = out.normalized() if out.length > 1e-3 else Vector((1, 0, 0))
    p = hp + out * 0.24 + Vector((0, 0, 0)) + Vector((0.02 * math.sin(f * 0.07), 0.02 * math.cos(f * 0.05), 0))
    z = cloth_z(p.x, p.y)
    if z is None: continue
    fd = out.copy(); fd.z = 0
    place_hand(WO, side, f, Vector((p.x, p.y, z)), Vector((0, 0, -1)), fd.normalized(), skin=0.008)
    apply_pose(WO, side, "flat_palm", f)
print("ARM_RESTS")
# 7. wall-bang 1180-1296: alternate real pushes (hand pulls back 10 cm between hits)
for i, f in enumerate(range(1185, 1291, 10)):
    s = "LR"[i % 2]; pb = WO.pose.bones["IK_hand." + s]
    sc.frame_set(f); M = pb.matrix.copy()
    M.translation += WO.matrix_world.inverted().to_3x3() @ Vector((0, -0.10, -0.03))
    pb.matrix = M; pb.keyframe_insert("location", frame=f, group=pb.name)
print("BANG_PUSHES")
# 4. 676-916: a hand already on a wall slides along it (feeling for a handle)
LINER = bpy.data.objects.get("BinLiner") or bpy.data.objects["BinShell"]
def bvh(o):
    ev = o.evaluated_get(dg()); me = ev.to_mesh(); mw = o.matrix_world
    t = BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons]); ev.to_mesh_clear(); return t
TL = bvh(LINER); nslide = 0
for s in "LR":
    fs = []
    for f in range(690, 905, 15):
        sc.frame_set(f); wr = W("wrist." + s); md = W("finger3-1." + s); palm = wr.lerp(md, 0.6)
        loc, n, i_, d = TL.find_nearest(palm, 0.08)
        if loc is not None: fs.append((f, loc, n))
    if len(fs) < 4: continue
    names = ["IK_hand." + s] + _chain(s)
    for g in (fs[0][0] - 10, fs[-1][0] + 10):
        sc.frame_set(g)
        for nm in names:
            pb = WO.pose.bones[nm]
            if nm.startswith("IK"): pb.keyframe_insert("location", frame=g, group=nm)
            pb.keyframe_insert("rotation_quaternion", frame=g, group=nm)
    for j, (f, loc, n) in enumerate(fs):
        nn = -n if (W("spine03") - loc).dot(n) < 0 else n           # normal pointing from the wall towards her
        tang = nn.cross(Vector((0, 0, 1))); tang = tang.normalized() if tang.length > 1e-3 else Vector((1, 0, 0))
        p = loc + tang * 0.08 * math.sin(j * 0.9) + Vector((0, 0, 0.04 * math.cos(j * 0.7)))
        place_hand(WO, s, f, p, -nn, Vector((0, 0, 1)), skin=0.008); apply_pose(WO, s, "flat_palm", f); nslide += 1
print("WALL_SLIDE", nslide)
sc["director_fix"] = "v007d: hard cuts past empty/black frames, eye-level face shots with fill light, 2 s cuts, moves on frozen holds"
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("V007D_DONE")
