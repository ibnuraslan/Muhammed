"""DonationBin v010 stage B: staging, acting, flap/latch/panel, lights, the one continuous camera. Built on the VO from the
start (beat frames from the v009 sync anchors: 1,115,265,451,673,847,1285,1465,1753,1867,1993; end 2388).
blender -b base.blend --python 02_animate.py -- <out.blend> [until_frame]"""
import bpy, bmesh, sys, math, random, json
from mathutils import Vector, Matrix, Quaternion, Euler
PIPE = "/home/user/Muhammed/blender/pipeline"
HERE = "/home/user/Muhammed/blender/DonationBin_v010/scripts"
exec(open(PIPE + "/anim_lib.py").read())
exec(open(PIPE + "/hand_poses.py").read())
sc = bpy.context.scene
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); LOG.append(s); print("LOG", s)
exec(open(HERE + "/lib_anim.py").read())
args = sys.argv[sys.argv.index("--") + 1:]
OUT = args[0]; UNTIL = int(args[1]) if len(args) > 1 else 2388
END = 2388
R_ = math.radians
for o in O:
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF': m.show_viewport = False

CH = list(sc["CH"]); CP = list(sc["CP"]); BX0, BX1, BY0, BY1, BZ1, T, FLOOR = list(sc["BIN"])
STAND = sc["stand_top"]
BLOBS = json.loads(sc["heap_blobs"])
IX0, IX1, IY0, IY1 = BX0 + T, BX1 - T, BY0 + T, BY1 - T
def heap(x, y):
    base = 0.05 + 0.26 * ((y - IY0) / (IY1 - IY0)) ** 0.8 if y > IY0 else 0.05
    h = 0.0
    for (bx, by, r, a_) in BLOBS:
        d2 = ((x - bx) ** 2 + (y - by) ** 2) / (r * r)
        if d2 < 4: h += a_ * math.exp(-d2)
    return FLOOR + base + h
HINGE = Vector((0.0, BY0 + 0.012, CH[3] - 0.012)); FLAP_L = CH[3] - CH[2] - 0.012
def flap_pt(a_deg, t, x=0.0):
    a = R_(a_deg); return HINGE + Vector((x, math.sin(a) * t, -math.cos(a) * t))
def flap_in_normal(a_deg):   # unit normal of the flap's INNER face (points into the bin when closed)
    a = R_(a_deg); return Vector((0, math.cos(a), math.sin(a)))

W = Actor(O["Woman"]); M = Actor(O["Man"]); P = Actor(O["Passer"]); F1 = Actor(O["Fire1"]); F2 = Actor(O["Fire2"])
UPZ = Vector((0, 0, 1))
# every actor is parked far off-set until its scene (make_human_ctrl reset them all to the origin)
for i, A_ in enumerate((P, F1, F2)):
    A_.key(1, pos=Vector((-14 - 2 * i, -16, 0.95)), rot=Rb((0, 0, 1), (0, -1, 0)))
def Rf(front, lean=0.0, side=0.0):
    """upright-ish orientation facing `front` (world), leaning forward `lean` deg"""
    fr = Vector(front).normalized(); up = (UPZ * math.cos(R_(lean)) + fr * math.sin(R_(lean)))
    q = Rb(up, fr)
    if side: q = Quaternion(fr, R_(side)) @ q
    return q
def LH(p, n, d): return ('L', p, n, d)       # body-local hand/foot spec
def WH(p, n, d): return ('W', p, n, d)       # world spec
# standard local specs (body frame: +X her left, -Y front, +Z up; origin = root bone head)
def hang(sx, fwd=0.0): return LH((sx * 0.22, -0.05 - fwd, -0.10), (-sx, 0, 0.1), (0.0, -0.25, -1))
def foot_stand(sx, fwd=0.0): return LH((sx * 0.10, -0.06 - fwd, -0.713), (0, 0, 1), (0, -1, 0))

# ==================================================================================== WOMAN
# A (1-115): ON the crate board, belly at the sill, leaning in; right hand rummages in the bin, left hand holds the flap in
WY = -1.16
WP_A = Vector((0.0, WY, STAND + 0.83))
FA = 35.0
def flap_hold(a_deg, t=0.25, x=-0.17):
    def spec(f): return WH(flap_pt(FLAP_ANG(f), t, x) - flap_in_normal(FLAP_ANG(f)) * 0.009, -flap_in_normal(FLAP_ANG(f)) * -1, (0, -math.sin(R_(FLAP_ANG(f))), math.cos(R_(FLAP_ANG(f)))))
    return spec
for f, dy, rh, hy in ((1, 0.0, (0.15, -0.60, 1.16), 0), (40, 0.01, (0.08, -0.57, 1.13), -12), (80, 0.0, (0.19, -0.61, 1.17), 10), (115, 0.01, (0.12, -0.58, 1.14), -4)):
    W.key(f, pos=WP_A + Vector((0, dy, 0)), rot=Rf((0, 1, 0), lean=3), spine=(6.0, 0.0, 0.0), head=(16.0, hy, 0.0),
          hand_R=WH(rh, (0, 0.15, -1), (0, 0.45, -1)), grip_R="relaxed",
          foot_L=WH((-0.10, WY - 0.01, STAND + 0.064 + 0.035), (0, 0.35, 0.94), (0, 0.94, -0.35)),
          foot_R=WH((0.10, WY - 0.03, STAND + 0.064 + 0.035), (0, 0.35, 0.94), (0, 0.94, -0.35)))

FLAP_KEYS = [(1, FA), (115, FA)]       # extended below; FLAP_ANG(f) reads them
def FLAP_ANG(f):
    ks = sorted(dict(FLAP_KEYS).items())
    return pchip([(k[0], k[1]) for k in ks])(f)
W.key(1, hand_L=flap_hold(FA), grip_L="flat_palm"); W.key(115, hand_L=flap_hold(FA))

# B (115-262): the shove. She pitches over the sill (pivot on her belly), the flap is pushed up by her back, she tumbles in
S = Vector((0.0, BY0 - 0.06, CH[2] + 0.03))
def pivot(th, slide=0.0, drop=0.0):
    rel = WP_A - S; c, s_ = math.cos(R_(th)), math.sin(R_(th))
    p = S + Vector((0, rel.y * c + rel.z * s_, -rel.y * s_ + rel.z * c)) + Vector((0, slide, -drop))
    q = Quaternion((1, 0, 0), R_(-th)) @ Rf((0, 1, 0), lean=3)
    return p, q
for f, th, sl, dr, fl, hp in ((128, 8, 0.0, 0.0, 34, 10), (140, 30, 0.02, 0.0, 44, 0), (152, 58, 0.06, 0.0, 50, -10),
                              (165, 85, 0.15, 0.0, 40, -15), (178, 105, 0.30, 0.02, 30, -10), (192, 122, 0.48, 0.06, 20, 0)):
    p, q = pivot(th, sl, dr)
    W.key(f, pos=p, rot=q, spine=(fl, 0.0, 0.0), head=(hp, 0.0, 0.0))
# hands go from the flap / bin into a brace in front of her head
W.key(140, hand_L=LH((0.20, -0.45, 0.30), (0, -0.3, -1), (0, -1, -0.2)), hand_R=LH((-0.20, -0.45, 0.30), (0, -0.3, -1), (0, -1, -0.2)), grip_L="open_alarm", grip_R="open_alarm")
W.key(192, hand_L=LH((0.24, -0.50, 0.45), (0, -1, 0), (0, 0, 1)), hand_R=LH((-0.24, -0.50, 0.45), (0, -1, 0), (0, 0, 1)))
# feet leave the board at ~140, knees fold
W.key(132, foot_L=WH((-0.10, WY - 0.01, STAND + 0.064 + 0.04), (0, 0.35, 0.94), (0, 0.94, -0.35)),
      foot_R=WH((0.10, WY - 0.03, STAND + 0.064 + 0.04), (0, 0.35, 0.94), (0, 0.94, -0.35)))
W.key(146, foot_L=LH((0.10, 0.12, -0.66), (0, 0.5, 0.8), (0, -0.8, 0.5)), foot_R=LH((-0.10, 0.14, -0.64), (0, 0.5, 0.8), (0, -0.8, 0.5)),
      knee_L=LH((0.18, -0.9, -0.1), (0, 0, 1), (0, 0, 1)), knee_R=LH((-0.18, -0.9, -0.1), (0, 0, 1), (0, 0, 1)))
W.key(165, foot_L=LH((0.10, 0.10, -0.68), (0, 0.8, 0.5), (0, -0.5, 0.8)), foot_R=LH((-0.10, 0.12, -0.67), (0, 0.8, 0.5), (0, -0.5, 0.8)))
W.key(192, foot_L=LH((0.10, 0.12, -0.66), (0, 0.8, 0.5), (0, -0.5, 0.8)), foot_R=LH((-0.11, 0.14, -0.65), (0, 0.8, 0.5), (0, -0.5, 0.8)))
# falling in: rolls onto her left side, along X, facing the front wall (-Y); lands ON the heap
LAND = Vector((-0.10, 0.12, 0.0)); LAND.z = heap(LAND.x, LAND.y) + 0.135
Q_LIE = Rb((1, 0, 0.12), (0, -1, 0.15))                  # head toward +X, chest toward -Y, lying on her LEFT side
W.key(212, pos=Vector((0.0, -0.25, 1.05)), rot=Rb((0.35, 0.4, -0.85), (0, -0.2, -1)), spine=(25, 0, 0), head=(-15, 0, 0),
      hand_L=LH((0.22, -0.35, 0.40), (0, -1, 0), (0, 0, 1)), hand_R=LH((-0.22, -0.35, 0.40), (0, -1, 0), (0, 0, 1)),
      foot_L=LH((0.10, 0.25, -0.50), (0, 0.6, 0.7), (0, -0.7, 0.6)), foot_R=LH((-0.11, 0.25, -0.48), (0, 0.6, 0.7), (0, -0.7, 0.6)))
W.key(232, pos=LAND + Vector((0.05, 0.0, 0.16)), rot=Rb((0.9, 0.1, -0.15), (0, -1, -0.5)), spine=(30, 0, 0), head=(-10, 0, 0))
W.key(246, pos=LAND + Vector((0, 0, 0.01)), rot=Q_LIE, spine=(38, 0, 0), head=(-8, 0, 0), grip_L="relaxed", grip_R="relaxed",
      hand_L=LH((0.16, -0.30, 0.22), (1, 0, 0), (0, -0.4, 1)), hand_R=LH((-0.10, -0.30, 0.18), (1, -0.2, 0), (0, -0.3, 1)),
      foot_L=LH((0.10, -0.35, -0.55), (0, 0.2, 1), (0, -1, 0)), foot_R=LH((-0.10, -0.30, -0.50), (0, 0.2, 1), (0, -1, 0)),
      knee_L=LH((0.20, -0.9, -0.2), (0, 0, 1), (0, 0, 1)), knee_R=LH((-0.20, -0.9, -0.2), (0, 0, 1), (0, 0, 1)))
W.key(256, pos=LAND, rot=Q_LIE)
# C (262-451): she lies stunned, stirs, pushes up on her hands and sits up facing the front wall
W.key(300, pos=LAND + Vector((0, 0, 0.005)), rot=Q_LIE, spine=(40, 0, 0), head=(-4, 0, 0))
W.key(330, pos=LAND, rot=Q_LIE, spine=(36, 0, 3), head=(-20, -10, 0))
SIT = Vector((-0.02, 0.18, 0.0)); SIT.z = heap(SIT.x, SIT.y) + 0.10
W.key(370, pos=LAND + Vector((-0.02, 0.02, 0.10)), rot=Rb((0.75, 0.0, 0.66), (0, -1, -0.1)), spine=(28, 0, 6), head=(-15, -5, 0),
      hand_R=WH((LAND.x - 0.05, LAND.y - 0.28, heap(LAND.x - 0.05, LAND.y - 0.28)), (0, 0, -1), (1, -0.2, 0)), grip_R="relaxed")
W.key(410, pos=SIT + Vector((0.08, 0, 0.02)), rot=Rb((0.25, 0.08, 1), (0, -1, 0)), spine=(18, 0, 0), head=(-25, 10, 0),
      hand_R=WH((SIT.x - 0.24, SIT.y + 0.05, heap(SIT.x - 0.24, SIT.y + 0.05)), (0, 0, -1), (0, -1, 0)),
      hand_L=WH((SIT.x + 0.25, SIT.y + 0.05, heap(SIT.x + 0.25, SIT.y + 0.05)), (0, 0, -1), (0, -1, 0)), grip_L="relaxed",
      foot_L=WH((SIT.x - 0.12, SIT.y - 0.42, heap(SIT.x - 0.12, SIT.y - 0.42) + 0.07), (0, 0, 1), (0, -1, 0)),
      foot_R=WH((SIT.x + 0.12, SIT.y - 0.40, heap(SIT.x + 0.12, SIT.y - 0.40) + 0.07), (0, 0, 1), (0, -1, 0)),
      knee_L=WH((SIT.x - 0.25, SIT.y - 0.9, 1.0), (0, 0, 1), (0, 0, 1)), knee_R=WH((SIT.x + 0.25, SIT.y - 0.9, 1.0), (0, 0, 1), (0, 0, 1)))
W.key(451, pos=SIT, rot=Rb((0, 0.05, 1), (0, -1, 0)), spine=(12, 0, 0), head=(-28, 0, 0))

# ==================================================================================== MAN: walks in, shoves her shoulders, backs off
MY = -1.64
def mpath(f):
    return catmull([(1, Vector((2.3, -2.9, 0))), (50, Vector((1.2, -2.2, 0))), (100, Vector((0.05, MY - 0.05, 0))), (112, Vector((0.03, MY, 0)))])(f)
M.walks.append((1, 112, mpath, None))
def myaw(f):
    if f >= 104: return 180.0
    d = mpath(f + 3) - mpath(f); return math.degrees(math.atan2(d.x, -d.y))
fl_, fr_ = walk_feet(M, mpath, myaw, 1, 112)
for f in range(1, 113, 4):
    p_ = mpath(f); yw = myaw(f); cyc = f / 38.0
    fr = Vector((math.sin(R_(yw)), -math.cos(R_(yw)), 0))
    M.key(f, pos=Vector((p_.x, p_.y, 0.94 - 0.012 * (0.5 + 0.5 * math.cos(4 * math.pi * cyc)))), rot=Rf(fr, lean=3),
          spine=(4.0, 6 * math.sin(2 * math.pi * cyc), 0.0), head=(4.0, 0.0, 0.0),
          hand_L=LH((0.22, -0.05 - 0.10 * math.sin(2 * math.pi * cyc), -0.12), (-1, 0, 0.1), (0, -0.25, -1)),
          hand_R=LH((-0.22, -0.05 + 0.10 * math.sin(2 * math.pi * cyc), -0.12), (1, 0, 0.1), (0, -0.25, -1)), grip_L="relaxed", grip_R="relaxed")
M.walks = []
M.key(1, foot_L=fl_, foot_R=fr_); M.key(112, foot_L=fl_, foot_R=fr_)
MF = Vector((0, 1, 0))
M.key(120, pos=Vector((0.03, MY + 0.04, 0.935)), rot=Rf(MF, lean=8), spine=(8, 0, 0), head=(8, 0, 0),
      foot_L=WH((-0.12, MY + 0.02, 0.074), (0, 0, 1), (0, 1, 0)), foot_R=WH((0.14, MY - 0.12, 0.074), (0, 0, 1), (0, 1, 0)))
def back_contact(sx, z_up):
    """palm ON her upper back (the sweater surface), found by a ray from behind at the moment being baked"""
    def spec(f):
        top = O["Woman.top"]; dg = bpy.context.evaluated_depsgraph_get(); e = top.evaluated_get(dg)
        sp = O["Woman"].matrix_world @ O["Woman"].pose.bones["spine01"].head
        org = Vector((sp.x + sx * 0.09, sp.y - 0.6, sp.z + z_up)); d = Vector((0, 1, 0))
        ok, loc, nrm, idx = e.ray_cast(e.matrix_world.inverted() @ org, d)
        p = (e.matrix_world @ loc) if ok else (sp + Vector((sx * 0.09, -0.12, z_up)))
        return WH(p, d, (0, 0.2, 1))
    return spec
M.key(121, hand_L=LH((0.18, -0.20, 0.32), (0, -1, 0), (0, -0.3, 1)), hand_R=LH((-0.18, -0.20, 0.32), (0, -1, 0), (0, -0.3, 1)), grip_L="flat_palm", grip_R="flat_palm")
M.key(128, hand_L=LH((0.20, -0.30, 0.40), (0, -1, 0), (0, -0.3, 1)), hand_R=LH((-0.20, -0.30, 0.40), (0, -1, 0), (0, -0.3, 1)))
M.key(134, pos=Vector((0.03, MY + 0.10, 0.93)), rot=Rf(MF, lean=14), spine=(12, 0, 0), hand_L=back_contact(-1, 0.02), hand_R=back_contact(1, 0.02),
      foot_L=WH((-0.12, MY + 0.12, 0.074), (0, 0, 1), (0, 1, 0)))
M.key(142, pos=Vector((0.03, MY + 0.12, 0.925)), rot=Rf(MF, lean=16), spine=(14, 0, 0), hand_L=back_contact(-1, 0.0), hand_R=back_contact(1, 0.0))
M.key(147, hand_L=LH((0.22, -0.24, 0.36), (0, -1, 0), (0, 0, 1)), hand_R=LH((-0.22, -0.24, 0.36), (0, -1, 0), (0, 0, 1)), grip_L="open_alarm", grip_R="open_alarm")
M.key(147, pos=Vector((0.25, MY - 0.15, 0.935)), rot=Rf((-0.3, 1, 0), lean=0), spine=(-2, 0, 0), head=(-8, -10, 0),
      foot_L=WH((0.10, MY - 0.05, 0.074), (0, 0, 1), (0, 1, 0)), foot_R=WH((0.42, MY - 0.30, 0.074), (0, 0, 1), (-0.3, 1, 0)))
M.key(160, pos=Vector((0.55, MY - 0.40, 0.94)), rot=Rf((-0.4, 1, 0), lean=-4), spine=(-4, 0, 0), head=(-12, -15, 0),
      foot_L=WH((0.45, MY - 0.32, 0.074), (0, 0, 1), (-0.4, 1, 0)), foot_R=WH((0.68, MY - 0.50, 0.074), (0, 0, 1), (-0.4, 1, 0)),
      hand_L=LH((0.26, -0.30, 0.38), (0, -1, 0), (0, 0, 1)), hand_R=LH((-0.26, -0.30, 0.38), (0, -1, 0), (0, 0, 1)))
M.key(176, pos=Vector((0.62, MY - 0.55, 0.94)), rot=Rf((-0.4, 1, 0), lean=-2), spine=(0, 0, 0), head=(-10, 0, 0),
      foot_L=WH((0.52, MY - 0.48, 0.074), (0, 0, 1), (-0.4, 1, 0)), foot_R=WH((0.74, MY - 0.62, 0.074), (0, 0, 1), (-0.4, 1, 0)),
      hand_L=hang(1, 0.05), hand_R=hang(-1, 0.05), grip_L="relaxed", grip_R="relaxed")
def mpath2(f): return catmull([(176, Vector((0.62, MY - 0.55, 0))), (220, Vector((1.3, -2.6, 0))), (262, Vector((2.4, -3.2, 0)))])(f)
def myaw2(f):
    d = mpath2(min(f + 3, 262)) - mpath2(f)
    return math.degrees(math.atan2(d.x, -d.y)) if d.length > 1e-4 else 120
fl2, fr2 = walk_feet(M, mpath2, myaw2, 182, 262)
for f in range(184, 263, 4):
    p_ = mpath2(f); yw = myaw2(f); cyc = f / 36.0; fr = Vector((math.sin(R_(yw)), -math.cos(R_(yw)), 0))
    M.key(f, pos=Vector((p_.x, p_.y, 0.94 - 0.012 * (0.5 + 0.5 * math.cos(4 * math.pi * cyc)))), rot=Rf(fr, lean=5), spine=(5, 6 * math.sin(2 * math.pi * cyc), 0),
          hand_L=LH((0.22, -0.05 - 0.12 * math.sin(2 * math.pi * cyc), -0.12), (-1, 0, 0.1), (0, -0.25, -1)),
          hand_R=LH((-0.22, -0.05 + 0.12 * math.sin(2 * math.pi * cyc), -0.12), (1, 0, 0.1), (0, -0.25, -1)))
M.key(184, foot_L=fl2, foot_R=fr2); M.key(262, foot_L=fl2, foot_R=fr2)

exec(open(HERE + "/02b_inside.py").read())
# ==================================================================================== bake (woman first: the man's hands read her back)
fs(1)
W.bake(1, UNTIL)
exec(open(HERE + "/snap_heap.py").read())
for A_ in (P, F1, F2): A_.bake(1, UNTIL)
M.bake(1, min(UNTIL, 262))
M.key(300, pos=Vector((16, -16, 0.95)), rot=Rb((0, 0, 1), (0, -1, 0))); M.key(299, pos=mpath2(262) + Vector((0, 0, 0.94)))
M.bake(299, 300)

# ==================================================================================== FLAP: pushed only by her hand / body; falls by gravity
FLAP = O["A_FlapHinge"]; FLAP.rotation_mode = 'XYZ'
def body_pts(obj_names):
    dg = bpy.context.evaluated_depsgraph_get(); pts = []
    for n in obj_names:
        o = O[n]; e = o.evaluated_get(dg); me = e.to_mesh()
        pts += [o.matrix_world @ v.co for v in me.vertices]
        e.to_mesh_clear()
    return pts
WPARTS = ["Woman.body", "Woman.top", "Woman.trousers"] + [c.name for c in O["Woman"].children if "ponytail" in c.name or "shoes" in c.name]
need = {}
for f in range(116, 262, 2):
    fs(f); pts = [p for p in body_pts(WPARTS) if abs(p.x) < 0.5 and p.y > BY0 - 0.02 and p.z > CH[2] - 0.05]
    amin = FA if f < 150 else 0.0
    for p in pts:
        r = Vector((0, p.y - HINGE.y, p.z - HINGE.z))
        if r.length > FLAP_L + 0.03 or r.length < 0.02: continue
        ang = math.degrees(math.atan2(r.y, -r.z))         # angle of this body point around the hinge, from straight down
        amin = max(amin, min(88.0, ang + math.degrees(0.025 / max(r.length, 0.05))))
    need[f] = amin
FLAP_KEYS[:] = [(1, FA), (115, FA)]
last = 115; prev = FA
for f in sorted(need):
    a = max(need[f], prev)        # the flap never 'sucks back' onto her while she passes (it rests open until 256)
    FLAP_KEYS.append((f, a)); prev = a; last = f
FLAP_KEYS[:] = [k for k in FLAP_KEYS if k[0] <= 256]
a0 = FLAP_KEYS[-1][1]
log("flap open angle at 256", round(a0, 1), "max", round(max(k[1] for k in FLAP_KEYS), 1))
# gravity fall from rest (theta ~ t^2), slam at 288, a small bounce
fall = [(256, a0), (264, a0 * 0.90), (272, a0 * 0.62), (280, a0 * 0.30), (287, 0.0), (291, 4.0), (295, 0.0)]
FLAP_KEYS += fall
for f in range(1, 300):
    FLAP.rotation_euler.x = R_(max(0.0, FLAP_ANG(f))); FLAP.keyframe_insert("rotation_euler", index=0, frame=f)
log("flap keyed: hand-held 35 deg, pushed by her back, falls 256-287, bounce 291")

# re-key the woman's left hand on the flap (she holds it at the flap's actual angle)
for f in range(1, 128, 2):
    fs(f); a = FLAP_ANG(f)
    p_ = flap_pt(a, 0.25, -0.17); n_ = flap_in_normal(a)
    place_hand(O["Woman"], "L", f, p_ - n_ * 0.009, n_, Vector((0, -math.sin(R_(a)), math.cos(R_(a)))), skin=0.024)

exec(open(HERE + "/02c_fx_camera.py").read())
open(OUT + ".log.txt", "w").write("\n".join(LOG))
for o_ in O:
    for m_ in getattr(o_, "modifiers", []):
        if m_.type == 'SUBSURF': m_.show_viewport = True
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("ANIM_OK", OUT)
