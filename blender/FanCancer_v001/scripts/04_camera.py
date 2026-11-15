"""One camera: Catmull-Rom spline through one framing per ~1 s. Set changes happen only while a surface fills the lens
(neck skin -> skin macro, phone screen -> city glow, lit window -> curtain, laptop screen -> rink)."""
import math
import bpy
from mathutils import Vector, Matrix

# ---- laptop on the coffee table, screen card on its lid
def world_bb(obs):
    pts = [o.matrix_world @ Vector(c) for o in obs for c in o.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])
bpy.context.view_layer.update()
tmn, tmx = world_bb([o for o in bpy.data.objects if o.parent and o.parent.name == "modern_coffee_table_01_root"])
lr = bpy.data.objects["classic_laptop_root"]; lr.location.z = tmx.z; bpy.context.view_layer.update()
lmn, lmx = world_bb([o for o in bpy.data.objects if o.parent == lr])
ls = bpy.data.objects["LaptopScreen"]
ls.location = Vector(((lmn.x + lmx.x) / 2, lmn.y + 0.035, lmn.z + (lmx.z - lmn.z) * 0.58))
ls.rotation_euler = (math.radians(90 - 12), 0, math.radians(180)); ls.scale = ((lmx.x - lmn.x) * 0.80 / 0.30,) * 2 + (1,)
LAPSCR = ls.location.copy()

def at(obj, f):
    sc.frame_set(f); return obj.matrix_world.translation.copy(), (obj.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
def bone_at(rig, bone, f):
    sc.frame_set(f); return rig.matrix_world @ rig.pose.bones[bone].head
mole3, moleN3 = at(bpy.data.objects["NeckMoleA"], F(5.0))
mole86, moleN86 = at(bpy.data.objects["NeckMoleA"], F(8.6))
moleB, moleBN = at(bpy.data.objects["NeckMoleB"], F(25.0))
fanH1 = bone_at(FR, "head", F(2.2)); fanH4 = bone_at(FR, "head", F(10.0)); fanH12 = bone_at(FR, "head", F(36.6))
manH = bone_at(MR, "head", F(19.4)); manBH = bone_at(MBR, "head", F(29.6)); docH = bone_at(DR, "head", F(25.8))
ph_p, ph_n = at(bpy.data.objects["ManPhone_screen"], F(31.8))
ph_n = (bpy.data.objects["ManPhone_screen"].matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
_dg = bpy.context.evaluated_depsgraph_get()
_hit = sc.ray_cast(_dg, ph_p + ph_n * 0.004, ph_n, distance=0.3)[0]
if _hit:
    ph_p, _n2 = at(bpy.data.objects["ManPhone_screenB"], F(31.8)); ph_n = (bpy.data.objects["ManPhone_screenB"].matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
print("PHONE_SIDE", "B" if _hit else "A")
fphone, fphoneN = at(bpy.data.objects["FanPhone_screen"], F(14.4))
ls_n = (ls.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
if ls_n.y < 0: ls_n = -ls_n      # approach from her side
ls.location = ls.location + ls_n * 0.012; LAPSCR = ls.location.copy()      # in front of the laptop's own screen glass
SK = Vector((200, 0, 0)); CT = Vector((-300, 0, 0)); HMv = Vector((-300, 200, 0))
INS = Vector((-300.0, -200.0, 1.0))   # v008: phone-screen insert set (built in 03e)
win = min((o for o in bpy.data.objects if o.name.startswith("Win_") and o.location.y > CT.y and abs(o.location.x - CT.x) < 20 and 3 < o.location.z < 6),
          key=lambda o: abs(o.location.x - CT.x), default=None)
_dgw = bpy.context.evaluated_depsgraph_get()
_h = sc.ray_cast(_dgw, CT + Vector((0, 0, 5.0)), Vector((0, 1, 0)), distance=40)
WIN = (_h[1] - Vector((0, 0.05, 0))) if _h[0] else CT + Vector((0, 13.9, 5.0))      # a lit window on the real north facade
print("WIN", WIN, _h[4].name if _h[0] else None)
if win:
    win.data = win.data.copy(); win.scale = (1, 1, 1)
    if win.animation_data: win.animation_data_clear()
V = Vector
def fill(p, n, d): return p + n * d
# (seconds, position, target, lens, jump_before)
K = [
    (0.0, V((4.0, -9.0, 3.6)), V((0.0, 2.5, 2.0)), 22, False),
    (1.0, V((2.2, -3.6, 2.6)), V((0.0, 0.6, 1.4)), 28, False),
    (1.7, V((1.2, -1.45, 1.9)), fanH1 + V((0, 0, -0.05)), 38, False),
    (1.95, V((0.30, -2.65, 2.75)), fanH1, 45, False),   # v010: further from him as he walks by
    (2.2, V((-0.6, -1.70, 2.65)), fanH1, 58, False),   # v010: high above his walk line
    (2.55, V((-0.80, -0.95, 2.95)), mole3, 36, False),
    (2.85, V((-0.40, 0.35, 2.80)), mole3, 40, False),                 # rises over the glass
    (3.3, V((0.05, 1.05, 1.95)), mole3, 70, False),                 # her POV over her shoulder; rack focus
    (3.9, V((0.15, 0.95, 1.88)), mole3, 85, False),
    (4.5, mole3 + V((0.05, 1.00, 0.30)), mole3 + V((0, 0, 0.08)), 58, False),   # v006: head and shoulders, mole visible
    (5.0, mole3 + V((0.05, 0.90, 0.27)), mole3 + V((0, 0, 0.08)), 62, False),
    (5.0, SK + V((0, 0, 15)), SK, 50, True),                          # through the skin
    (5.6, SK + V((0.5, -4.0, 9.0)), SK + V((0, -3.5, 0)), 45, False),
    (6.4, SK + V((2.5, -14.0, 1.5)), SK + V((0, -6, -1.2)), 40, False),
    (7.3, SK + V((-3.5, -11.5, -1.8)), SK + V((0.5, -6, -1.9)), 45, False),
    (8.2, SK + V((-0.8, -8.6, 0.8)), SK + V((0, -6, -0.6)), 50, False),
    (8.6, SK + V((0, -1.0, 15)), SK, 50, False),
    (8.6, fill(mole86, moleN86, 0.015), mole86, 50, True),           # back out through the skin
    (8.78, fill(mole86, moleN86, 0.14), mole86, 50, False),           # straight pull-back off the mole before the swing
    (9.2, V((0.80, -0.30, 1.40)), fanH4, 42, False),
    (10.2, V((0.40, -0.25, 1.22)), fanH4, 45, False),
    (11.2, V((-0.50, -0.22, 1.32)), fanH4, 45, False),
    (12.2, V((-0.22, -0.22, 1.30)), fanH4, 50, False),
    (13.0, V((-0.20, -0.45, 1.38)), fanH4 + V((0, 0, 0.02)), 45, False),
    (13.6, V((-0.45, -0.32, 1.35)), (fphone + fanH4) / 2, 36, False),                # through the glass to her right side
    (14.3, V((-0.32, -0.26, 1.27)), (fphone + fanH4) / 2, 36, False),               # top-down on the thumbs
    (15.2, V((-0.18, -0.30, 1.32)), (fphone + fanH4) / 2, 34, False),
    (15.8, V((-0.50, -0.42, 1.45)), V((0.0, 0.3, 1.4)), 32, False),
    (16.4, V((-0.95, -0.95, 1.65)), V((0.0, 0.05, 1.45)), 30, False),   # the slap, wide
    (17.0, V((0.30, -1.35, 2.25)), V((0.1, -0.2, 1.55)), 30, False),     # over the glass to his side
    (17.4, V((1.25, -1.05, 2.05)), manH, 38, False),          # swing wide of his head
    (17.8, V((1.10, -0.20, 1.72)), manH, 40, False),          # his face as he reads
    (18.6, V((0.95, -1.55, 2.05)), V((-0.05, 0.0, 1.45)), 34, False),  # wide over his shoulder, phone on the glass
    (19.0, V((-0.85, -1.35, 1.95)), manH, 36, False),   # arc wide around him, never past his head
    (19.4, V((-0.40, -0.20, 1.50)), manH, 40, False),                 # his puzzled face
    (19.8, V((-0.95, -1.60, 1.85)), manH, 36, False),   # back out the way it came, behind him
    (20.2, V((1.10, -1.60, 1.60)), manH + V((0, 0, -0.2)), 30, False),
    (21.0, V((1.20, -0.95, 2.20)), V((-1.0, -0.8, 1.2)), 32, False),
    (21.6, V((-0.6, -0.95, 2.35)), V((-4.0, -1.0, 1.2)), 30, False),   # v008: high, clear of the bench players
    (22.18, V((-1.4, -0.95, 2.35)), V((-5.5, -1.0, 1.2)), 30, False),
    (22.2, V((-26.1, -0.85, 1.80)), V((-28.6, -2.2, 1.20)), 30, True),   # v008: clean cut to the clinic (beat 8)
    (23.6, V((-26.3, -0.75, 1.70)), V((-28.6, -2.2, 1.25)), 30, False),
    (24.3, V((-29.55, -0.95, 1.85)), moleB, 34, False),   # v006: from his left front, the doctor stands clear beside him
    (25.0, V((-29.75, -1.00, 1.80)), moleB + V((0, 0.12, -0.08)), 38, False),
    (25.45, V((-28.30, -0.75, 1.90)), docH, 45, False),   # v008: her face over his shoulder from 1.25 m
    (25.8, V((-28.60, -0.70, 1.90)), docH, 45, False),
    (26.6, V((-30.3, -1.20, 2.0)), moleB, 45, False),
    (27.4, V((-29.55, -1.0, 1.85)), moleB, 30, False),   # v007: she is seen whole beside him
    (28.3, V((-29.50, -1.10, 1.65)), (moleB + manBH) / 2, 30, False),               # front-left: the bandage pressed on
    (29.2, V((-27.6, -0.90, 1.55)), manBH, 45, False),                # relief
    (30.79, V((-27.75, -0.85, 1.50)), manBH, 45, False),
    (30.8, V((-28.40, -0.70, 1.35)), V((-28.49, -1.95, 1.20)), 38, True),   # v008: beat 10, he types the post, face lit by the screen
    (33.38, V((-28.62, -0.76, 1.32)), V((-28.49, -1.95, 1.18)), 44, False),
    (33.4, INS + V((0, -1.0, 0)), INS, 33, True),                  # insert: the post with her photo, share icons pulsing
    (34.58, INS + V((0, -0.93, 0)), INS, 33, False),
    (34.6, HMv + V((0.95, 0.25, 1.2)), fanH12, 35, True),          # her at the laptop
    (35.5, HMv + V((0.95, 0.18, 1.17)), fanH12, 35, False),
    (36.5, HMv + V((0.95, 0.15, 1.15)), fanH12, 35, False),
    (37.2, HMv + V((-0.45, 0.55, 1.05)), fanH12, 50, False),
    (37.5, HMv + V((0.60, 0.70, 1.15)), fanH12, 34, False),   # her face as she stares at the call   # her laptop, the call on screen
    (37.98, HMv + V((0.55, 0.75, 1.15)), fanH12, 34, False),   # v006: hold on her at the laptop
    (38.0, FIN + V((-0.38, -1.62, 1.78)), FIN + V((-0.33, 0, 1.12)), 38, True),   # v009: 1.6 m at chest height, knees up, slow push
    (39.7, FIN + V((-0.35, -1.50, 1.76)), FIN + V((-0.33, 0, 1.13)), 38, False),
    (41.5, FIN + V((-0.33, -1.40, 1.74)), FIN + V((-0.33, 0, 1.14)), 39, False),
]
cqo = bpy.data.objects["Cheque"]
for f in range(F(38.0), 2641, 4):
    sc.frame_set(f)
    wl = FR.matrix_world @ FR.pose.bones["wrist.L"].head; wr = FR.matrix_world @ FR.pose.bones["wrist.R"].head
    xa = (wl - wr); xa.z = 0; xa.normalize(); mid = (wl + wr) / 2
    cqo.location = mid + Vector((0, 0, -0.02)); cqo.rotation_euler = (0, 0, math.atan2(xa.y, xa.x))
    cqo.keyframe_insert("location", frame=f); cqo.keyframe_insert("rotation_euler", frame=f)
segs = [[]]
for k in K:
    if k[4] and segs[-1]: segs.append([])
    segs[-1].append(k)
cd = bpy.data.cameras.new("FilmCam"); cam = bpy.data.objects.new("FilmCam", cd); sc.collection.objects.link(cam); sc.camera = cam
cd.clip_start = 0.002; cd.clip_end = 600; cd.sensor_fit = 'AUTO'; cd.sensor_width = 36
cd.dof.use_dof = True
cam.rotation_mode = 'QUATERNION'
spans = []
for si, sg in enumerate(segs):
    f0 = F(sg[0][0]); f1 = F(segs[si + 1][0][0]) - 1 if si + 1 < len(segs) else sc.frame_end
    pos = catmull([(F(t), p) for t, p, _, _, _ in sg]); tgt = catmull([(F(t), q) for t, _, q, _, _ in sg])
    lens = catmull([(F(t), float(l)) for t, _, _, l, _ in sg])
    spans.append((f0, f1, pos, tgt, lens))
glassP = V((0.0, 0.0, 1.5))
prevq = None
for f0, f1, pos, tgt, lens in spans:
    for f in range(f0, f1 + 1):
        p = pos(f); q_ = tgt(f); d = q_ - p
        q = d.to_track_quat('-Z', 'Y')
        if prevq is not None and prevq.dot(q) < 0: q = -q
        prevq = q
        cam.location = p; cam.rotation_quaternion = q
        cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_quaternion", frame=f)
        cd.lens = lens(f); cd.keyframe_insert("lens", frame=f)
        dist = d.length
        t = (f - 1) / 60.0
        if 2.9 <= t <= 3.6:          # rack focus: glass -> his neck
            u = smooth((t - 3.0) / 0.5); dg = (glassP - p).length
            dist = dg + (dist - dg) * u
        cd.dof.focus_distance = max(0.005, dist); cd.dof.keyframe_insert("focus_distance", frame=f)
        cd.dof.aperture_fstop = 64.0 if p.x > 150 else (32.0 if dist < 0.3 else 8.0)
        cd.dof.keyframe_insert("aperture_fstop", frame=f)
# jumps must be hard: constant interpolation on the frame before each jump
for f in range(F(37.6), F(38.0)):
    sc.frame_set(f); p_ = cam.matrix_world.translation.copy(); d_ = (p_ - LAPSCR).dot(ls_n)
    if d_ < 0.011:
        p_ = p_ + ls_n * (0.011 - d_); cam.location = p_
        cam.rotation_quaternion = (LAPSCR - p_).to_track_quat('-Z', 'Y'); cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_quaternion", frame=f)
JUMPS = [sp[1] for sp in spans[:-1]]
for idb in (cam, cd):
    for fc in _fcurves(idb.animation_data.action):
        for kp in fc.keyframe_points:
            if int(round(kp.co.x)) in JUMPS: kp.interpolation = 'CONSTANT'
# world per set
for f, v in ((1, (0, 0, 0)), (F(22.2), (1, 0, 0)), (F(34.6), (1, 1, 1)), (F(38.0), (0, 0, 0))):
    wkey(f, *v)
for fc in _fcurves(sc.world.node_tree.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
# skin backdrop + cutaway only seen by the camera when there
sc.frame_set(1)
print("CAM_OK", len(segs), "segments")
