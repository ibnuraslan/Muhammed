"""Animation: bullet, wall break-through, couple (03a/03b), tumbler impact FX, continuous camera (03c).
blender -b scene.blend --python 03_animate.py -- <out.blend>"""
import sys, os, math, random
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler
HERE = os.path.dirname(os.path.abspath(__file__)); PIPE = os.path.join(HERE, "..", "..", "pipeline")
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; R_ = math.radians
exec(open(os.path.join(HERE, "layout.py")).read())
TOP = sc["table_top"]
def smooth(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def kf(o, path, f, val=None, idx=-1):
    if val is not None:
        setattr(o, path, val) if not isinstance(val, (int, float)) or idx < 0 else None
    o.keyframe_insert(path, frame=f, index=idx)
def set_interp(obj, kind="LINEAR", data=False):
    ad = (obj.data.animation_data if data else obj.animation_data)
    if not ad or not ad.action: return
    for layer in ad.action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    for kp in fc.keyframe_points: kp.interpolation = kind

# ------------------------------------------------------------------ the shot line
CUP = bpy.data.objects["Tumbler"]; C3 = Vector((CUP_C.x, CUP_C.y, IMPACT_Z))
def r_out(z):
    pts = [(0.0, 0.039), (0.008, 0.0405), (0.06, 0.0405), (0.075, 0.0425), (0.235, 0.0505), (0.25, 0.051)]
    for (z0, r0), (z1, r1) in zip(pts, pts[1:]):
        if z <= z1: return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return pts[-1][1]
DXY = Vector((1.0, SHOT_SLOPE, 0)).normalized()
IMP = C3 - DXY * r_out(IMPACT_Z - sc["cup_top"])               # the point on the steel that gets hit
S0 = Vector((-14.0, IMP.y + (-14.0 - IMP.x) * SHOT_SLOPE, SHOT_Z0))
D = (IMP - S0).normalized()                           # flight direction
SV = Vector((-D.y, D.x, 0)).normalized()              # left of travel
NOSE = 0.0075
def on_line(x):                                       # bullet centre at a given x
    t = (x - S0.x) / D.x; return S0 + D * t
HOLE = on_line(-0.09)
sc["hole"] = HOLE; sc["impact"] = IMP
print("SHOT", S0, "HOLE", HOLE, "IMPACT", IMP)
exec(open(os.path.join(PIPE, "anim_lib.py")).read().split("# ------------------------------------------------------------------ terrain")[0])
# x of the bullet centre over time (speed ramps: fast outside, extreme slow motion from the wall on)
X_IMPACT = IMP.x - NOSE * D.x
BX = pchip([(1, -14.0), (60, -8.2), (110, -2.6), (139, WALL_OUT - NOSE - 0.002), (200, -0.10), (262, 0.03), (271, 0.06),
            (391, 0.62), (607, 1.95), (973, X_IMPACT)])
def P(f):
    if f <= F_IMPACT: return on_line(BX(f))
    return BPOST(f)
# after the impact: pops back 9 cm (slow), drops off the table edge (y=-0.42), then real time from f1285: fall, bounces, settle
TABLE_EDGE_Y = TABLE_C.y - 0.705 * TABLE_SY
p_imp = on_line(X_IMPACT)
REB = p_imp - DXY * 0.085 + Vector((0, -0.04, 0))
LAND = Vector((REB.x - 0.42, REB.y - 0.06, 0.0046))
BOUNCES = [(1285, REB + Vector((0, 0, -0.06))), (1306, LAND + Vector((0.03, 0.01, 0))), (1322, LAND + Vector((-0.03, -0.01, 0.0))),
           (1333, LAND + Vector((-0.08, -0.01, 0))), (1341, LAND + Vector((-0.1, -0.01, 0))), (1395, LAND + Vector((-0.16, 0.0, 0)))]
def BPOST(f):
    if f <= 1120:                       # pop back, slow-mo
        u = smooth((f - F_IMPACT) / (1120 - F_IMPACT)); return p_imp.lerp(REB, u) + Vector((0, 0, 0.012 * math.sin(math.pi * u)))
    if f <= 1285:                       # drift down past the table edge (slow-mo gravity)
        u = (f - 1120) / (1285 - 1120); return REB + Vector((0, 0, -0.06 * u * u))
    # real time: free fall from f1285 to the floor, then bounces
    pts = BOUNCES
    for (fa, pa), (fb, pb) in zip(pts, pts[1:]):
        if f <= fb:
            u = (f - fa) / (fb - fa); h = {0: 0.0}.get(0)
            base = pa.lerp(pb, u)
            if fa == 1285:              # parabolic drop
                z = pa.z + (pb.z - pa.z) * u * u; return Vector((base.x, base.y, z))
            hop = {1306: 0.05, 1322: 0.018, 1333: 0.005}.get(fa, 0.0)
            return base + Vector((0, 0, hop * 4 * u * (1 - u)))
    return pts[-1][1]
BUL = bpy.data.objects["Bullet"]; WAKE = bpy.data.objects["BulletWake"]
BUL.rotation_mode = "QUATERNION"
qd = D.to_track_quat("X", "Z")
for f in range(1, END + 1, 1):
    p = P(f); BUL.location = p; BUL.keyframe_insert("location", frame=f)
    if f <= F_IMPACT:
        spin = (f - 1) * (0.9 if f < 139 else 0.12)           # rifling spin, slows with the time-warp
        q = qd @ Quaternion((1, 0, 0), spin)
    elif f <= 1285:
        u = (f - F_IMPACT) / (1285 - F_IMPACT)
        q = qd @ Quaternion((0, 0, 1), R_(160) * smooth(u * 1.6)) @ Quaternion((1, 0, 0), R_(300) * u) @ Quaternion((0, 1, 0), R_(70) * u)
    else:
        u = min(1.0, (f - 1285) / 110.0)
        q = qd @ Quaternion((0, 0, 1), R_(160) + R_(400) * smooth(u)) @ Quaternion((1, 0, 0), R_(300) + R_(200) * smooth(u)) @ Quaternion((0, 1, 0), R_(70) + R_(20) * smooth(u))
        if f >= 1341: q = qd @ Quaternion((0, 0, 1), R_(560) + R_(60) * smooth((f - 1341) / 54)) @ Quaternion((1, 0, 0), R_(90))   # rolls, then lies on its side
    if BUL.rotation_quaternion.dot(q) < 0: q = -q
    BUL.rotation_quaternion = q; BUL.keyframe_insert("rotation_quaternion", frame=f)
mk = BUL.data.shape_keys.key_blocks["Mushroom"]
for f, v in ((1, 0), (F_IMPACT, 0), (F_IMPACT + 18, 0.85), (F_IMPACT + 40, 1.0)):
    mk.value = v; mk.keyframe_insert("value", frame=f)
# wake: long while fast, short shimmer in slow-mo, gone at impact
for f, sx in ((1, 1.0), (120, 1.0), (150, 0.35), (271, 0.3), (F_IMPACT - 4, 0.25), (F_IMPACT, 0.0)):
    WAKE.scale = (sx, 1, 1); WAKE.keyframe_insert("scale", frame=f)

exec(open(os.path.join(HERE, "03b_fx.py")).read())
exec(open(os.path.join(HERE, "03a_humans.py")).read())
exec(open(os.path.join(HERE, "03d_acting.py")).read())
exec(open(os.path.join(HERE, "03c_camera.py")).read())
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ANIMATED", OUT)
