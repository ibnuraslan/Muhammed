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
    v = p - c; h = ray(c, v, v.length)
    return h is None or (h[1] - c).length > v.length - 0.10 or h[4].name in own

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

A1=(30,);A2=(-30,)

# 09c: three shots that 09 could not place well
#  601-675 (no front shot fits while she gets up facing the front wall): a profile at her eye level
#  1561-1860: the three-days shots alternate between two clearly different angles (09 found the same spot twice)
PREV = None
ok = face_shot(601, 675, (90, -90, 80, -80, 100, -100, 70, -70, 110, -110), (0.62, 0.56, 0.50, 0.45, 0.40), ups=(0.0, -0.10, 0.10, -0.20, 0.20), lens=18, name="stands profile")
if not ok:
    fixed_shot(601, 675, (0.58, 0.40, 1.60), (0.25, -0.35, 1.45), lens=18, track=(lambda f, _t=smooth_face(WO, 601, 675): _t[f]), name="stands corner")
face_shot(1561, 1670, (-30, -25, -35, -20, -40), (0.62, 0.55, 0.48), ups=(0.0, 0.08, -0.05), lens=24, push=0.04, name="daysA")
face_shot(1671, 1770, (-65, -60, -70, -55, -75, 5, 0, 10), (0.55, 0.48, 0.42), ups=(0.30, 0.25, 0.35, 0.20), lens=22, push=0.04, name="daysB")
face_shot(1771, 1860, (-30, -25, -35, -20, -40), (0.62, 0.55, 0.48), ups=(0.0, 0.08, -0.05), lens=26, push=0.06, name="daysA2")
for f, (p, q, ln) in sorted(NEW.items()):
    cam.location = p; cam.keyframe_insert("location", frame=f)
    cam.rotation_mode = 'QUATERNION'
    q0 = cam.rotation_quaternion.copy()
    cam.rotation_quaternion = q if q.dot(q0) >= 0 else -q; cam.keyframe_insert("rotation_quaternion", frame=f)
    cd.lens = ln; cd.keyframe_insert("lens", frame=f)
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("V007D_C_DONE", len(NEW))
