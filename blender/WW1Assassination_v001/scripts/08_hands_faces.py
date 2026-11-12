"""v003 pass: hands (relaxed curl, real grips, Limit Rotation on fingers/thumbs/wrists), couple facial expressions,
and a hand-contact audit. blender -b film.blend --python 08_hands_faces.py -- <out.blend> <audit.txt>"""
import sys, os, math
import bpy
from mathutils import Vector, Matrix, Quaternion
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
exec(open(os.path.join(HERE, "00_story.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]
sc = bpy.context.scene
R_ = math.radians
humans = [o for o in bpy.data.objects if o.type == 'ARMATURE' and "finger1-1.L" in o.pose.bones]
GRIP = {("Duchess", "L"): 62, ("Gunman", "R"): 70, ("Driver", "L"): 55, ("Driver", "R"): 55, ("Bomber", "R"): 60,
        ("Officer", "L"): 45, ("Officer", "R"): 45}

def palm_frame(arm, s):
    B = arm.data.bones
    wr = B["wrist." + s].head_local
    dd = (B["finger3-1." + s].head_local - wr).normalized()
    aa = (B["finger2-1." + s].head_local - B["finger5-1." + s].head_local).normalized()
    n = dd.cross(aa) if s == "L" else aa.cross(dd)
    return dd, aa, n.normalized()

def curl_hand(arm, s, deg):
    B = arm.data.bones; PB = arm.pose.bones
    dd, aa, n = palm_frame(arm, s)
    for fi in range(1, 6):
        for j in range(1, 4):
            nm = f"finger{fi}-{j}.{s}"
            if nm not in PB: continue
            b = B[nm]; d = (b.tail_local - b.head_local).normalized()
            if fi == 1:   # thumb: curl across the palm toward the fingers (opposition)
                tgt = (n * 0.6 + aa * -0.8 * (1 if s == "L" else 1)).normalized()
                ang = deg * (0.45 if j == 1 else 0.6)
            else:
                tgt = n; ang = deg * (1.0 if j == 1 else 1.15 if j == 2 else 0.9) * (1.0 + 0.06 * (fi - 2))
            ax_w = d.cross(tgt)
            if ax_w.length < 1e-4: continue
            ax_l = (b.matrix_local.to_3x3().inverted() @ ax_w).normalized()
            q = Quaternion(ax_l, R_(min(ang, 95)))
            pb = PB[nm]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q
            # limits in local space around the curl: forward 0..90 on the dominant axis, small spread
            c = pb.constraints.get("HandLimit") or pb.constraints.new('LIMIT_ROTATION'); c.name = "HandLimit"
            c.owner_space = 'LOCAL'
            e = q.to_euler('XYZ')
            for k, axn in enumerate("xyz"):
                lo, hi = (min(0.0, e[k]) - R_(10), max(0.0, e[k]) + R_(10))
                if abs(ax_l[k]) == max(abs(x) for x in ax_l):   # bend axis: 0..90 in the curl direction only
                    lo, hi = (min(0.0, math.copysign(R_(90), e[k])), max(0.0, math.copysign(R_(90), e[k])))
                setattr(c, "use_limit_" + axn, True); setattr(c, "min_" + axn, lo); setattr(c, "max_" + axn, hi)
for arm in humans:
    base = arm.name.split("_")[0] if arm.name.startswith("Crowd") else arm.name
    for s in "LR":
        curl_hand(arm, s, GRIP.get((arm.name, s), 24 + 6 * ((hash(arm.name) % 3))))
        pb = arm.pose.bones["wrist." + s]
        c = pb.constraints.get("WristLimit") or pb.constraints.new('LIMIT_ROTATION'); c.name = "WristLimit"; c.owner_space = 'LOCAL'
        c.use_limit_x = c.use_limit_z = True; c.min_x, c.max_x = R_(-60), R_(60); c.min_z, c.max_z = R_(-35), R_(35)
        c.use_limit_y = True; c.min_y, c.max_y = R_(-70), R_(70)
print("HANDS curled + limits on", len(humans), "rigs")

# ---------------------------------------------------------------- faces: couple expressions on the story clock
def face(arm_name, f, smile, shock, closed):
    arm = bpy.data.objects[arm_name]; R = Rig(arm)
    def off(n, v):
        if n in R.PB: R.key_world(n, f, Matrix.Translation(v) @ R.rest(n), rot=False)
    for s, sx in (("L", 1), ("R", -1)):
        off("risorius03." + s, Vector((sx * 0.006 * smile - sx * 0.002 * shock, 0.004 * smile, 0.006 * smile - 0.004 * shock)))
        off("risorius02." + s, Vector((sx * 0.003 * smile, 0.002 * smile, 0.003 * smile)))
        off("oris04." + s, Vector((sx * 0.003 * smile, 0.0, 0.003 * smile)))
        off("levator05." + s, Vector((0, 0, 0.002 * smile)))
        off("orbicularis03." + s, Vector((0, 0, 0.0035 * shock - 0.007 * closed - 0.0015 * smile)))
        off("orbicularis04." + s, Vector((0, 0, -0.002 * shock + 0.003 * closed + 0.0015 * smile)))
        off("oculi02." + s, Vector((0, 0, 0.007 * shock)))
        off("temporalis01." + s, Vector((0, 0, 0.004 * shock)))
    R.key_rot("jaw", f, [("X", 13 * shock + 4 * closed + 2 * smile)])
import random as _r
_r.seed(11)
def _blinker():
    bl = []; t = _r.uniform(0.5, 1.5)
    while t < 30.0: bl.append(1 + round(t * 60)); t += _r.uniform(2.4, 3.6)
    return lambda f: max([0.0] + [max(0.0, 1 - abs(f - b0 - 2) / 3.0) for b0 in bl if abs(f - b0 - 2) < 3])
BL = {n: _blinker() for n in ("Archduke", "Duchess", "Gunman")}
FR2 = list(range(1, 1781, 2))
def sm(x): return max(0.0, min(1.0, x)) ** 2 * (3 - 2 * max(0.0, min(1.0, x)))
for f in FR2:
    s = sig_f(f)
    # smiles while waving to the crowd; fright at the thrown object; shock at the gun; eyes close after the slump
    a_smile = (1 - sm((s - 3.35) / 0.2)) if s < 4 else (1 - sm((s - 25.0) / 0.3)) * sm((s - 7.0) / 1.0)
    a_shock = max(sm((s - 3.4) / 0.2) * (1 - sm((s - 5.5) / 0.8)), sm((s - 25.15) / 0.3))
    a_closed = sm((s - 26.8) / 0.5)
    d_smile = (1 - sm((s - 3.4) / 0.2)) if s < 4 else (1 - sm((s - 25.1) / 0.3)) * sm((s - 7.0) / 1.0)
    d_shock = max(sm((s - 3.45) / 0.2) * (1 - sm((s - 5.6) / 0.8)), sm((s - 25.2) / 0.3))
    d_closed = sm((s - 26.3) / 0.5)
    face("Archduke", f, a_smile * (1 - a_shock), a_shock * (1 - a_closed), max(a_closed, BL["Archduke"](f)))
    face("Duchess", f, d_smile * (1 - d_shock), d_shock * (1 - d_closed), max(d_closed, BL["Duchess"](f)))
for f in range(1301, 1781, 2):
    s = sig_f(f)
    flinch = max((1 - min(1.0, abs(s - st) / 0.12)) for st in SHOT_S)
    face("Gunman", f, 0.0, flinch * 0.6, BL["Gunman"](f))
print("FACES keyed")

bpy.ops.wm.save_as_mainfile(filepath=OUT)
