"""One continuous camera (CAM_Film) on a Catmull-Rom path through keyed framings (~1 per second).
blender -b anim.blend --python 04_camera.py -- <out.blend>"""
import sys, os, math
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib.py")).read())
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
V = lambda *a: Vector(a)
for o in [o for o in bpy.data.objects if o.type == 'CAMERA']:
    bpy.data.objects.remove(o, do_unlink=True)

def head(name, f, dz=0.0):
    ev(f); r = bpy.data.objects[name]; pb = r.pose.bones["head"]
    return r.matrix_world @ (pb.head + (pb.tail - pb.head) * 0.35) + V(0, 0, dz)
LIV = bpy.data.objects["Liver"]
def liv(f, off=V(0, 0, 0.084)):
    ev(f); return LIV.matrix_world @ (V(0, 0, 0.084)) + off - V(0, 0, 0.084) + V(0, 0, 0)
def brand(f, ch="S"):
    ob = bpy.data.objects["Brand_%s_Sear" % ch]; ev(f)
    pts = [ob.matrix_world @ V(p.co[0], p.co[1], p.co[2]) for p in ob.data.splines[0].points]
    return sum(pts, V(0, 0, 0)) / len(pts)
WINP = V(-0.28, -0.06, 1.16)
S1H = lambda f: head("Surgeon1", f)
S2H = lambda f: head("Surgeon2", f)
PTH = lambda f: head("Patient", f)
CAL = bpy.data.objects["Calendar"].matrix_world.translation.copy()
SZ = -6.0
LZ = LIV.location.z + 0.084

K = [  # frame, camera position, aim point, lens (mm)
    # 1 - OR mid-surgery, crane down past the lamp, over his shoulder onto the pen, dive into the window
    # v007: open across the table on the surgeon's masked face and the pen, then swing round his right side
    (1, V(-0.05, 0.55, 1.78), S1H(1) + V(0, 0.05, -0.10), 28),
    (40, V(0.45, 0.2, 2.02), S1H(40) + V(0.1, 0.3, -0.3), 28),
    (80, V(0.5, -0.5, 1.98), WINP + V(0, 0, 0.05), 32),
    (115, V(0.12, -0.12, 1.56), WINP + V(0, 0, -0.02), 36),
    (132, V(-0.27, -0.10, 1.26), WINP + V(0, 0.02, -0.4), 30),
    (138, V(-0.28, -0.07, -2.5), V(-0.25, -0.06, -6.0), 28),
    (142, V(-0.12, -0.2, LZ + 0.40), V(-0.05, -0.05, LZ), 32),
    # studio macro: S, then B, then the whole liver
    (152, V(-0.06, -0.30, LZ + 0.30), V(-0.03, -0.03, LZ + 0.02), 38),
    (170, V(-0.11, -0.19, LZ - 0.01), brand(200, "S"), 52),
    (205, V(-0.03, -0.17, LZ - 0.025), brand(200, "S") + V(0, 0, 0.01), 58),
    (240, V(0.09, -0.18, LZ - 0.015), brand(260, "B") + V(0, 0, 0.01), 56),
    (262, V(0.03, -0.30, LZ + 0.02), V(0.0, -0.03, LZ), 48),
    (272, V(0.0, -0.22, LZ + 0.40), V(0.0, -0.05, LZ + 0.7), 35),
    # 2 - rise back out of the window, stitching top-down, crane to his face, mask down, smile
    (277, V(-0.12, -0.14, -2.5), V(-0.2, -0.1, 1.0), 30),
    (281, V(-0.28, -0.08, 1.21), V(-0.28, -0.06, 2.5), 30),
    (292, V(-0.27, -0.12, 1.50), WINP, 34),
    (330, V(-0.30, 0.0, 1.47), WINP, 38),
    (365, V(0.02, -0.02, 1.50), WINP + V(0.02, 0, 0), 40),
    (410, V(0.30, -0.15, 1.62), (WINP + S1H(420)) / 2, 30),
    (455, V(0.25, 0.25, 1.68), S1H(470), 36),
    (500, V(-0.05, 0.10, 1.68), S1H(500), 50),
    (545, V(-0.22, 0.02, 1.66), S1H(540), 56),
    # 3 - whip-pan to the calendar, drift, through the wall
    (568, V(0.05, -0.1, 1.68), S1H(560) + V(0.5, 0, 0), 45),
    (586, V(1.9, -0.7, 1.6), CAL, 40),
    (612, V(2.7, -0.95, 1.56), CAL, 44),
    (632, V(3.2, -0.6, 1.5), CAL + V(2.5, 0.6, -0.2), 34),
    # 4 - home: she buckles, mug drops, x-ray glow on her side
    (648, V(4.15, -0.55, 1.25), V(5.95, -0.3, 1.0), 26),
    (672, V(4.5, -1.2, 0.7), V(5.95, -0.3, 1.0), 26),
    (700, V(5.0, -1.25, 0.85), V(5.95, -0.3, 0.95), 30),
    (732, V(5.15, -1.25, 0.95), V(5.9, -0.38, 0.95), 32),
    (756, V(5.0, -0.75, 1.15), V(5.95, -0.3, 0.85), 30),
    (770, V(4.4, 0.55, 1.35), V(3.0, 0.6, 1.3), 28),
    # 5 - back through the wall into the OR: bed bursts through the doors, surgeon 2 steps in
    (784, V(3.0, 0.6, 1.35), V(1.7, 3.6, 1.1), 22),
    (830, V(3.05, 0.55, 1.35), V(1.75, 3.4, 0.9), 24),
    (870, V(2.95, 1.45, 0.85), V(1.75, 3.0, 0.85), 22),
    (910, V(2.5, 0.2, 0.75), V(1.0, 2.2, 1.0), 22),
    (950, V(0.85, 1.25, 0.45), V(-1.0, 1.6, 1.3), 22),
    (990, V(0.5, 0.95, 1.2), V(-0.3, 0.68, 1.4), 26),
    (1025, V(-0.05, -0.25, 1.45), S2H(1020) + V(0, 0, -0.2), 30),
    # 6 - dive into the window again: gloved hands lift the liver into the light; out to her widening eyes
    (1046, V(-0.25, -0.12, 1.42), WINP, 34),
    (1057, V(-0.28, -0.07, 1.21), WINP + V(0, 0, -0.5), 30),
    (1060, V(-0.28, -0.065, -2.5), V(-0.25, -0.06, -6.0), 28),
    (1064, V(-0.02, -0.25, LZ + 0.40), V(0.0, -0.02, LZ), 32),
    (1078, V(0.05, -0.42, LZ + 0.25), V(0.0, -0.02, LZ + 0.02), 34),
    (1105, V(-0.16, -0.36, LZ + 0.06), V(0.0, -0.02, LZ + 0.08), 40),
    (1122, V(0.10, -0.42, LZ + 0.12), V(0.0, -0.02, LZ + 0.14), 42),
    (1140, V(-0.06, -0.42, LZ + 0.20), brand(1150, "S") + V(0.03, 0, -0.01), 46),
    (1168, V(0.03, -0.38, LZ + 0.24), brand(1168, "S") + V(0.03, 0, -0.01), 52),
    (1178, V(0.0, -0.15, LZ + 0.40), V(0.0, -0.1, LZ + 2.0), 35),
    (1182, V(-0.15, -0.1, -2.5), V(-0.2, -0.08, 1.0), 33),
    (1186, V(-0.28, -0.08, 1.21), V(-0.28, 0.2, 2.2), 30),
    (1191, V(-0.28, -0.08, 1.42), V(-0.28, 0.5, 1.6), 30),
    (1199, V(-0.29, -0.05, 1.55), S2H(1200), 38),
    (1210, V(-0.30, 0.02, 1.62), S2H(1210), 42),
    (1228, V(-0.30, 0.05, 1.58), S2H(1225), 52),
    # 7 - whip-pan through the west wall into the hearing room: anatomy wall, orbit to the confessing surgeon
    (1231, V(-0.33, 0.07, 1.80), V(-1.6, 0.4, 1.95), 42),
    (1235, V(-0.45, 0.1, 1.9), V(-2.4, 0.25, 1.9), 40),
    (1242, V(-0.95, 0.15, 1.92), V(-6.0, 0.0, 1.75), 40),
    (1254, V(-3.3, 0.0, 1.62), V(-8.0, 0.0, 1.6), 28),
    (1270, V(-5.3, -1.6, 1.75), V(-4.35, -1.1, 1.75), 30),
    (1300, V(-5.7, 0.3, 1.75), V(-4.6, 0.9, 1.7), 28),
    (1320, V(-5.65, 1.15, 1.7), V(-6.75, 0.0, 1.5), 30),
    (1335, V(-5.9, 1.4, 1.65), V(-6.75, 0.0, 1.55), 30),
    (1370, V(-7.55, 1.15, 1.55), S1H(1370), 34),
    (1405, V(-7.8, 0.35, 1.45), S1H(1405), 42),
    (1440, V(-7.75, -0.75, 1.3), S1H(1440) + V(0.2, 0, -0.1), 36),
    (1458, V(-7.85, -0.45, 1.3), V(-7.9, 1.6, 1.35), 30),
    (1478, V(-8.3, -0.35, 1.25), V(-10.3, 0.0, 1.55), 24),
    # 8 - gavel slams, the license gets the red stamp, push in and settle
    (1510, V(-9.0, 0.55, 1.5), V(-10.05, 0.22, 1.25), 32),
    (1545, V(-9.35, 0.45, 1.45), V(-10.04, 0.2, 1.22), 40),
    (1566, V(-9.4, 0.15, 1.5), V(-10.04, 0.1, 1.2), 38),
    (1590, V(-9.45, -0.6, 1.55), V(-10.05, -0.95, 1.2), 40),
    (1615, V(-9.55, -0.80, 1.52), V(-10.05, -1.0, 1.19), 44),
    (1655, V(-9.68, -0.90, 1.48), V(-10.05, -1.0, 1.19), 46),
    (1685, V(-9.70, -1.04, 1.43), V(-10.05, -0.99, 1.19), 50),
    (1710, V(-9.72, -1.14, 1.41), V(-10.05, -0.98, 1.19), 54),
]
cam_d = bpy.data.cameras.new("CAM_Film"); cam_d.sensor_fit = 'AUTO'; cam_d.clip_start = 0.005; cam_d.clip_end = 60
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 4.0
cam = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(cam); sc.camera = cam
aim = bpy.data.objects.get("CAM_Film_Aim") or bpy.data.objects.new("CAM_Film_Aim", None)
if aim.name not in sc.collection.objects:
    sc.collection.objects.link(aim)
tt = cam.constraints.new('TRACK_TO'); tt.target = aim; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
cam_d.dof.focus_object = aim
def pvec(keys):
    fx = [pchip([(f, v[i]) for f, v in keys]) for i in range(3)]
    return lambda t: V(fx[0](t), fx[1](t), fx[2](t))
def blend(keys):
    p_ = pvec(keys); c_ = catmull(keys)
    return lambda t: (p_(t) + c_(t)) * 0.5
fc = blend([(f, c) for f, c, a, l in K]); fa = blend([(f, a) for f, c, a, l in K]); fl = pchip([(f, float(l)) for f, c, a, l in K])
# transit snapping: the camera never sits inside a wall, floor or the gap between the OR table and the studio.
# Frames that would be inside a slab are moved to the nearer face, so each pass-through is a single textured frame.
MEMB_Z = LZ + 0.45
def body_h(x, y):
    u = (x + 0.15) / 0.75; v = y / 0.36
    torso = 0.27 * max(0.0, 1 - u * u) ** 0.5 * max(0.0, 1 - v ** 4) if abs(u) < 1 else 0.0
    legs = 0.14 * max(0.0, 1 - (y / 0.3) ** 2) if 0.4 < x < 1.15 else 0.0
    return max(torso, legs)
ZONES = [  # axis, lo, hi, extra condition
    ('x', 3.488, 3.812, lambda p: abs(p.y) < 3.0 and 0 < p.z < 2.7),
    ('x', -3.912, -3.488, lambda p: abs(p.y) < 3.5 and 0 < p.z < 3.0),
]
def snap(f, p, prev_side):
    q = p.copy()
    for ax, lo, hi, cond in ZONES:
        v = getattr(q, ax)
        if lo < v < hi and cond(q):
            side = prev_side.get((ax, lo)) or ('lo' if v < (lo + hi) / 2 else 'hi')
            if (side == 'lo' and v > (lo + hi) / 2) or (side == 'hi' and v < (lo + hi) / 2):
                side = 'hi' if side == 'lo' else 'lo'
            setattr(q, ax, lo if side == 'lo' else hi)
        elif v <= lo: prev_side[(ax, lo)] = 'lo'
        elif v >= hi: prev_side[(ax, lo)] = 'hi'
    top = 0.95 + 0.012 + body_h(q.x, q.y) - 0.012       # just under the abdomen skin / drape
    if abs(q.x) < 0.8 and abs(q.y) < 0.8 and MEMB_Z - 0.012 < q.z < top + 0.024:
        mid = (MEMB_Z + top) / 2; key = 'dive'
        side = prev_side.get(key) or ('hi' if q.z > mid else 'lo')
        if (side == 'hi' and q.z < mid) or (side == 'lo' and q.z > mid):
            side = 'lo' if side == 'hi' else 'hi'
        q.z = top + 0.024 if side == 'hi' else MEMB_Z - 0.012      # just under the membrane: it fills the frame looking up
    elif q.z >= top + 0.024: prev_side['dive'] = 'hi'
    elif q.z <= MEMB_Z - 0.012: prev_side['dive'] = 'lo'
    return q
PS = {}
for f in range(1, 1711):
    cam.location = snap(f, fc(f), PS); cam.keyframe_insert("location", frame=f)
    aim.location = fa(f); aim.keyframe_insert("location", frame=f)
    if f % 2 or f == 1710:
        cam_d.lens = fl(f); cam_d.keyframe_insert("lens", frame=f)
# macro: deeper DOF in the studio, shallower close-ups
for f, fs in ((1, 4.0), (150, 8.0), (300, 8.0), (318, 4.0), (1060, 4.0), (1075, 8.0), (1185, 8.0), (1195, 3.2), (1240, 4.0)):
    cam_d.dof.aperture_fstop = fs; cam_d.dof.keyframe_insert("aperture_fstop", frame=f)
sc["camera_keys"] = [k[0] for k in K]
print("CAMERA_DONE", len(K))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
