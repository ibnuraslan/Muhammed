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
def look_q(c, t, up=None):
    if up is None: return (t - c).to_track_quat('-Z', 'Y')
    fw_ = (t - c).normalized(); u_ = (up - fw_ * up.dot(fw_)).normalized(); x_ = fw_.cross(u_)
    return Matrix((x_, u_, -fw_)).transposed().to_quaternion()
def headup(r, f):
    sc.frame_set(f); hb = r.pose.bones["head"]; M = r.matrix_world
    return (M @ hb.tail - M @ hb.head).normalized()
def face_shot(f0, f1, angs, dists, ups=(0.0, -0.06, 0.08, 0.16, 0.25), lens=24, B=INSIDE, push=0.0, r=WO, aim=Vector((0, 0, -0.04)), name="", above=-9.0, roll=False):
    """fixed camera on her face side at eye level; tracks the smoothed face; optional slow push-in"""
    fm, fw = headpos(r, (f0 + f1) // 2)
    fh = Vector((fw.x, fw.y, 0)); fh = fh.normalized() if fh.length > 0.2 else Vector((0, -1, 0))
    tr = smooth_face(r, f0, f1)
    HU = {}
    if roll:
        raw = {f: headup(r, f) for f in range(f0 - 12, f1 + 13)}
        HU = {f: sum((raw[g] for g in range(f - 12, f + 13)), Vector()).normalized() for f in range(f0, f1 + 1)}
    own = set(c.name for c in r.children_recursive)
    for d in dists:
        for a in angs:
            for u in ups:
                c = fm + (Matrix.Rotation(math.radians(a), 3, 'Z') @ fh) * d + Vector((0, 0, u))
                if not inbox(c, B) or c.z - fm.z < above: continue
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
                    NEW[f] = [cc, look_q(cc, tr[f] + aim, HU[f] if roll else None), lens]
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


A1 = (0, 20, -20, 30, -30, 40, -40, 50, -50, 60, -60)
# 3. 331-420: from above her eye line (no chest-up low angle)
face_shot(331, 420, A1, (0.62, 0.56, 0.50), ups=(0.30, 0.40, 0.25, 0.50, 0.20), lens=24, above=0.15, name="sit A high")
# 2. 1561-1860: she lies on her side: camera rolls with her head so her face reads upright, tighter lens
#    (no legs or arm filling the frame); two alternating angles
cuts = [1561, 1671, 1771, 1861]
for i, (a_, b_) in enumerate(zip(cuts, cuts[1:])):
    angs = (0, 15, -15, 25, -25, 35, -35) if i % 2 == 0 else (-40, 40, -50, 50, -30, 30, -60, 60)
    face_shot(a_, b_ - 1, angs, (0.62, 0.56, 0.50, 0.45), ups=(0.0, 0.06, 0.12, -0.04, 0.20), lens=38, push=0.03, roll=True, aim=Vector(), name="days roll%d" % i)
# 5. 2096-2125: crawl-out seen from the left, clear of FireB (who walks in on the right)
fixed_shot(2096, 2125, (-0.85, -2.05, 1.00), (0.0, -0.55, 0.45), (-0.80, -2.10, 1.08), (0.0, -0.75, 0.60), lens=24, name="crawl left")
for f, (p, q, ln) in sorted(NEW.items()):
    cam.location = p; cam.keyframe_insert("location", frame=f)
    cam.rotation_mode = 'QUATERNION'
    q0 = cam.rotation_quaternion.copy()
    cam.rotation_quaternion = q if q.dot(q0) >= 0 else -q; cam.keyframe_insert("rotation_quaternion", frame=f)
    cd.lens = ln; cd.keyframe_insert("lens", frame=f)
# 2104-2126: her knees and palms sat in the fallen cut panel -> the whole body rides 4 cm higher (eased)
BN = ["root", "IK_hand.L", "IK_hand.R", "IK_foot.L", "IK_foot.R", "Pole_elbow.L", "Pole_elbow.R", "Pole_knee.L", "Pole_knee.R"]
for g in (2098, 2132):
    sc.frame_set(g)
    for b in BN: WO.pose.bones[b].keyframe_insert("location", frame=g, group=b)
for f in range(2102, 2129, 2):
    w = min(1.0, (f - 2098) / 6.0, (2132 - f) / 6.0)
    sc.frame_set(f)
    for b in BN:
        pb = WO.pose.bones[b]; M = pb.matrix.copy()
        M.translation += WO.matrix_world.inverted().to_3x3() @ Vector((0, 0, 0.045 * w))
        pb.matrix = M
    for b in BN: WO.pose.bones[b].keyframe_insert("location", frame=f, group=b)
print("CRAWL_LIFT")
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("V007D_E_DONE", len(NEW))
