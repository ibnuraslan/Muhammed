"""(helpers from 09_v007d_patch) DonationBin v007d patch, applied to the packed v007c file (director review of 7677a55).
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
    """strict (09d): the first thing the ray meets must be within 12 cm of her face - no own torso, legs or arms in front"""
    for o_ in (Vector(), Vector((0.06, 0, 0)), Vector((-0.06, 0, 0)), Vector((0, 0, 0.06)), Vector((0, 0, -0.08))):
        q = p + o_; v = q - c; h = ray(c, v, v.length + 0.2)
        if h is not None and (h[1] - q).length > 0.12 and (h[1] - c).length < v.length: return False
    return True

# ---------------------------------------------------------------- current camera, per frame
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


A1 = (30, -30, 40, -40, 20, -20, 50, -50, 60, -60, 0, 70, -70)
A2 = (-30, 30, -40, 40, -20, 20, -50, 50, -60, 60, 0, -70, 70)
UPS = (0.0, 0.08, 0.16, 0.25, 0.35, 0.45, -0.06)
# 3. 331-420 again: strict visibility (no chest in front of the face)
face_shot(331, 420, A1, (0.62, 0.56, 0.50, 0.45), ups=UPS, lens=24, name="sit A strict")
# 2. 1471-1860 again: strict visibility, eye level / slightly above, two alternating angles
cuts = [1471, 1561, 1671, 1771, 1861]
for i, (a_, b_) in enumerate(zip(cuts, cuts[1:])):
    if not face_shot(a_, b_ - 1, A1 if i % 2 == 0 else A2, (0.62, 0.56, 0.50, 0.45, 0.40), ups=UPS, lens=24, push=0.03, name="days strict%d" % i):
        fixed_shot(a_, b_ - 1, (-0.40, -0.30, 1.75), (0.45, 0.28, 0.80), lens=24, track=(lambda f, _t=smooth_face(WO, a_, b_ - 1): _t[f]), name="days fallback%d" % i)
# 5. 2031-2075: the passer-by walked through the second angle -> a left-side wide clear of everyone
fixed_shot(2031, 2075, (-1.70, -2.90, 1.60), (0.20, -0.80, 0.95), lens=24, name="cutting left wide")
# 5. 2096-2125: side view of her crawling out (not the top of her head)
fixed_shot(2096, 2125, (1.15, -1.75, 0.95), (0.0, -0.55, 0.45), (1.05, -1.85, 1.05), (0.0, -0.75, 0.60), lens=22, name="crawl side")
for f, (p, q, ln) in sorted(NEW.items()):
    cam.location = p; cam.keyframe_insert("location", frame=f)
    cam.rotation_mode = 'QUATERNION'
    q0 = cam.rotation_quaternion.copy()
    cam.rotation_quaternion = q if q.dot(q0) >= 0 else -q; cam.keyframe_insert("rotation_quaternion", frame=f)
    cd.lens = ln; cd.keyframe_insert("lens", frame=f)
# 2096-2128: her palms rest ON the fallen cut panel (they sank into it)
exec(open("/home/user/Muhammed/blender/pipeline/hand_poses.py").read())
CP = bpy.data.objects["CutPanel"]
def panel_top(x, y):
    inv = CP.matrix_world.inverted()
    h, loc, n, i = CP.ray_cast(inv @ Vector((x, y, 1.0)), (inv.to_3x3() @ Vector((0, 0, -1))).normalized())
    return (CP.matrix_world @ loc).z if h else None
def Wb(b): pb = WO.pose.bones[b]; return WO.matrix_world @ pb.head
np_ = 0
for s in "LR":
    names = ["IK_hand." + s] + _chain(s)
    for g in (2092, 2132):
        sc.frame_set(g)
        for nm in names:
            pb = WO.pose.bones[nm]
            if nm.startswith("IK"): pb.keyframe_insert("location", frame=g, group=nm)
            pb.keyframe_insert("rotation_quaternion", frame=g, group=nm)
    for f in range(2098, 2130, 3):
        sc.frame_set(f); wr = Wb("wrist." + s); md = Wb("finger3-1." + s); palm = wr.lerp(md, 0.6)
        z = panel_top(palm.x, palm.y)
        if z is None or palm.z - z > 0.10: continue
        fd = md - wr; fd.z = 0
        place_hand(WO, s, f, Vector((palm.x, palm.y, z)), Vector((0, 0, -1)), fd.normalized() if fd.length > 1e-3 else Vector((0, -1, 0)), skin=0.010)
        apply_pose(WO, s, "flat_palm", f); np_ += 1
print("PALMS_ON_PANEL", np_)
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("V007D_D_DONE", len(NEW))
