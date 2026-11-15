"""All 16 shots as 1x clips (each ~30% longer than its beat), one camera per shot, hard cuts by camera markers.
blender -b build/sets.blend --python 03_anim.py [-- timing.json]
timing.json (Phase 2): {"S01": [cut_in, cut_out], ...}. Without it the clips run back to back at full length (Phase 1)."""
import bpy, os, sys, json, math, random
from mathutils import Vector, Matrix
D = os.path.dirname(__file__)
exec(open(D + "/common.py").read())
exec(open(PIPE + "/anim_lib.py").read()); exec(open(PIPE + "/hand_poses.py").read()); exec(open(D + "/lib.py").read())
R = math.radians
sc = bpy.context.scene
sc.render.fps = 60; sc.render.resolution_x = 1080; sc.render.resolution_y = 1920
cams = bpy.data.collections.get("CAMS") or bpy.data.collections.new("CAMS")
if cams.name not in sc.collection.children: sc.collection.children.link(cams)

# ------------------------------------------------------------------ shot table: (id, expected beat seconds)
SHOTS = [("S01", 2.0), ("S02", 1.5), ("S03", 1.5), ("S04", 1.5), ("S05", 1.5), ("S06", 1.5), ("S07", 1.5), ("S08", 2.0),
         ("S09", 1.5), ("S10", 2.0), ("S11", 2.0), ("S12", 2.0), ("S13", 2.0), ("S14", 1.5), ("S15", 2.0), ("S16", 2.0)]
CLIP = {k: int(round(1.3 * s * 60)) for k, s in SHOTS}
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if argv:
    T = {k: tuple(v) for k, v in json.load(open(argv[0])).items()}
else:
    T = {}; f = 1
    for k, s in SHOTS: T[k] = (f, f + CLIP[k]); f += CLIP[k]
FEND = max(v[1] for v in T.values()) - 1
sc.frame_start = 1; sc.frame_end = FEND

man = Man("SodaMan"); sci = Man("Scientist")
O = bpy.data.objects
can, plate, pud, beaker, liq, jel, tray, spat, mouse, stream, tail = (O[n] for n in ("SodaCan", "Plate", "SodaPuddle", "Beaker", "BeakerLiquid", "Jelly", "Tray", "Spatula", "Mouse", "PourStream", "MouseTailTip"))
bubbles = [o for o in O if o.name.startswith("Bubble.")]
TZ = sc["TABLE_Z"]; LZ = sc["LAB_Z"]; LX = sc["LX"]
MAN_XY = (0.0, 0.42); SCI_XY = (LX, 0.34)

def begin(objs, t):
    """hard cut at t: every channel of objs holds its value at t-1 (CONSTANT) and loses keys >= t"""
    for o in objs:
        for fc in all_fcurves(o):
            v = fc.evaluate(t - 1)
            for k in [k for k in fc.keyframe_points if k.co.x >= t - 1 - 1e-3]: fc.keyframe_points.remove(k, fast=True)
            fc.update(); kp = fc.keyframe_points.insert(t - 1, v); kp.interpolation = 'CONSTANT'
    for o in objs:
        for c in o.constraints:
            if c.type == 'CHILD_OF':
                c.influence = 0.0; c.keyframe_insert("influence", frame=t)
                for fc in all_fcurves(o):
                    if fc.data_path.startswith('constraints'):
                        for k in fc.keyframe_points: k.interpolation = 'CONSTANT'

PROPS = [can, plate, pud, beaker, jel, tray, spat, mouse, stream, tail, liq] + bubbles
def park(t, keep=()):
    """everything not used by the shot goes off-set (and hidden) at t"""
    for o in PROPS:
        if o in keep or o.parent in keep: continue
        if o.parent is None or o.parent not in PROPS: key_obj(o, t, loc=(0, -20, -5))
        vis(o, t, False)

def show(o, t): vis(o, t, True)

def lip_now(m):
    return head_point(m, mouth_rest(m))

def base_man(m, t, xy, yaw=0.0):
    m.stand(t, xy, yaw); m.spine(t); m.jaw(t, 0); m.eyes(t)
    for s in "LR": m.hang(s, t)

def ease(u): return smooth(u)

def track(clip_t0, n, step, fn):
    for i in range(0, n + 1, step):
        fn(clip_t0 + i, i / n)

def mark(k, c):
    t = T[k][0]; mk = sc.timeline_markers.new(k, frame=t); mk.camera = c

def catch(c, d=0.06, energy=1.5):
    """small camera-carried catchlight for the eyes (face fill stays well under 10 W)"""
    nm = c.name + "_Catch"
    L = O.get(nm) or bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'POINT'))
    if L.name not in cams.objects: cams.objects.link(L)
    L.data.energy = energy; L.data.shadow_soft_size = 0.02; L.parent = c; L.location = (0, d, 0)
    L.data.use_shadow = False

ALL = [man.o, sci.o] + PROPS

# ===================================================================== S01 drinking (kitchen, side MCU)
def S01(t, L):
    begin(ALL, t); park(t, keep=(can,)); show(can, t)
    base_man(man, t, MAN_XY); man.spine(t, flex=-2, pitch=-6); man.eyes(t, pitch=-4)
    sc.frame_set(t)
    lip = lip_now(man)
    C0 = can_frame((0, 0.35, 0.94), lip + Vector((0, -0.08, -0.13)))
    key_matrix(can, t, C0); sc.frame_set(t)
    a = C0.to_3x3() @ Vector((0, 0, 1)); org = C0.translation
    grip_object(man.o, "R", t, can, org + a * 0.05 + Vector((-0.033, 0, 0)), (1, 0, 0), finger_dir=Vector((0, -1, 0.15)))
    H = Held(can, man, "R"); H.grab(t)
    def fr(f, u):
        k = ease(min(1, u / 0.25))                   # 0..1 lift to the lips in the first quarter
        d = ease(max(0, (u - 0.2) / 0.8))            # drinking tilt after
        man.spine(f, flex=-2 - 4 * d, pitch=-6 - 18 * k - 8 * d, turn=0)
        man.stand(f, MAN_XY, side=0.0, flex=-2 * d)
        sc.frame_set(f); lip = lip_now(man)
        a = Vector((0, 0.35 + 0.35 * k + 0.25 * d, 0.94 - 0.30 * k - 0.25 * d))
        off = Vector((0, -0.08, -0.13)) * (1 - k)
        Wm = H.wrist_for(can_frame(a, lip + off))
        sh = man.r.PB["upperarm01.R"].head
        hand_target(man, "R", f, Wm, pole=Vector((sh.x - 0.55, sh.y + 0.25, sh.z - 0.35)))
        man.eyes(f, pitch=-4 + 6 * k)
    track(t, L, 6, fr)
    c = cam("CAM_S01", 55, 9); catch(c)
    sc.frame_set(t + L // 2); lp = lip_now(man)
    look(c, t, lp + Vector((0.72, -0.50, 0.02)), lp + Vector((0.0, -0.02, -0.08)))
    look(c, t + L, lp + Vector((0.58, -0.40, 0.05)), lp + Vector((0.0, -0.02, -0.06)))
    mark("S01", c)

# ===================================================================== S02 macro: can top, mouse tail tip in the opening (can on table)
CAN_TABLE = Vector((-0.22, -0.02, TZ))
def S02(t, L):
    begin(ALL, t); park(t, keep=(can,)); show(can, t); show(tail, t)
    base_man(man, t, MAN_XY); man.spine(t, flex=14, pitch=22)       # leaning over, out of focus behind
    man.spine(t + L, flex=16, pitch=24)
    key_matrix(can, t, Matrix.Translation(CAN_TABLE) @ Matrix.Rotation(R(200), 4, 'Z'))
    c = cam("CAM_S02", 70, 11); top = CAN_TABLE + Vector((0, 0, 0.122))
    # the opening sits on the can's +Y side, rotated 200 deg -> faces the camera side
    look(c, t, top + Vector((0.05, -0.16, 0.27)), top + Vector((0.0, -0.004, 0.0)))
    look(c, t + L, top + Vector((0.03, -0.09, 0.16)), top + Vector((0.0, -0.006, 0.0)))
    mark("S02", c)

# ===================================================================== S03 hero can on the table, man behind leaning on the table
def S03(t, L):
    begin(ALL, t); park(t, keep=(can,)); show(can, t)
    key_matrix(can, t, Matrix.Translation(CAN_TABLE) @ Matrix.Rotation(R(20), 4, 'Z'))
    man.stand(t, MAN_XY); man.spine(t, flex=8, pitch=22); man.jaw(t, 0); man.eyes(t, pitch=12)
    man.spine(t + L, flex=10, pitch=26, turn=-6)
    for s in "LR": man.hang(s, t); man.hang(s, t + L)
    c = cam("CAM_S03", 30, 8)
    look(c, t, Vector((0.02, -0.72, 0.90)), Vector((-0.08, 0.3, 1.22)))
    look(c, t + L, Vector((-0.10, -0.62, 0.89)), Vector((-0.08, 0.3, 1.24)))
    mark("S03", c)

# ===================================================================== S04 recoil: man lowers the can, sees the mouse on the plate, pulls back
PLATE_P = Vector((0.08, -0.16, TZ))
def mouse_on_plate(t):
    key_obj(plate, t, loc=PLATE_P, rot=(0, 0, 0)); show(plate, t)
    key_obj(pud, t, loc=PLATE_P + Vector((0, 0, 0.0102)), rot=(0, 0, R(30))); show(pud, t)
    key_obj(mouse, t, loc=PLATE_P + Vector((0.0, 0.0, 0.0102 + 0.0215)), rot=(0, R(90), R(25))); show(mouse, t)
def S04(t, L):
    begin(ALL, t); park(t, keep=(can, plate, pud, mouse)); show(can, t); mouse_on_plate(t)
    base_man(man, t, MAN_XY)
    man.spine(t, flex=12, pitch=20); man.eyes(t, pitch=12)
    sc.frame_set(t)
    C0 = Matrix.Translation(Vector((-0.30, 0.02, 1.08))) @ Matrix.Rotation(R(-10), 4, 'X')
    key_matrix(can, t, C0); sc.frame_set(t)
    grip_object(man.o, "R", t, can, C0.translation + Vector((-0.033, 0, 0.055)), (1, 0, 0), finger_dir=Vector((0, -1, 0)))
    H = Held(can, man, "R"); H.grab(t)
    def fr(f, u):
        r = ease(min(1, max(0, (u - 0.25) / 0.3)))   # recoil after a short look
        man.stand(f, (MAN_XY[0] + 0.0, MAN_XY[1] + 0.10 * r), flex=-6 * r)
        man.spine(f, flex=12 - 22 * r, pitch=20 - 22 * r, turn=-18 * r, side=-4 * r)
        man.eyes(f, pitch=12 - 6 * r, yaw=8 * r)
        man.jaw(f, 3 * r)
        sc.frame_set(f)
        Cw = Matrix.Translation(Vector((-0.30 - 0.04 * r, 0.02 + 0.12 * r, 1.08 + 0.06 * r))) @ Matrix.Rotation(R(-10), 4, 'X')
        sh = man.r.PB["upperarm01.R"].head
        hand_target(man, "R", f, H.wrist_for(Cw), pole=Vector((sh.x - 0.45, sh.y + 0.5, sh.z - 0.3)))
        # free hand comes up open in disgust at chest height (palm out)
        shL = man.r.PB["upperarm01.L"].head
        if r > 0.0:
            W = Vector((shL.x + 0.02, shL.y - 0.30 * r - 0.05, shL.z - 0.42 + 0.22 * r))
            man.hand("L", f, W, Vector((0.1, -0.3, 1)), Vector((0, -1, 0.2)), pole=Vector((shL.x + 0.4, shL.y + 0.3, shL.z - 0.4)))
        elif f == t:
            man.hang("L", f)
    track(t, L, 6, fr)
    apply_pose(man.o, "L", "relaxed", t); apply_pose(man.o, "L", "open_alarm", t + int(0.45 * L))
    c = cam("CAM_S04", 32, 8)
    look(c, t, Vector((0.25, -1.75, 1.32)), Vector((0.0, 0.2, 1.12)))
    look(c, t + L, Vector((0.18, -1.55, 1.30)), Vector((0.0, 0.25, 1.15)))
    catch(c, energy=2.0)
    mark("S04", c)

# ===================================================================== S05 "so he sued": leans on the table, points at the plate
def S05(t, L):
    begin(ALL, t); park(t, keep=(can, plate, pud, mouse)); mouse_on_plate(t); show(can, t)
    key_matrix(can, t, Matrix.Translation(CAN_TABLE))
    man.stand(t, MAN_XY); man.spine(t, flex=8, pitch=6); man.jaw(t, 0); man.eyes(t)
    man.hang("L", t); man.hang("L", t + L)
    man.hang("R", t)
    def fr(f, u):
        p = ease(min(1, u / 0.35))
        man.spine(f, flex=8 + 6 * p, pitch=6 + 4 * p, turn=6 * p)
        man.jaw(f, 3 * math.sin(math.pi * min(1, u * 1.6)))
        if p > 0:
            sc.frame_set(f); sh = man.r.PB["upperarm01.R"].head
            tip = PLATE_P + Vector((0, 0.06, 0.18))
            W = sh.lerp(tip, 0.25 + 0.55 * p) + Vector((0, 0, -0.18 * (1 - p)))
            d = (tip - W).normalized()
            man.hand("R", f, W, d, Vector((0.2, 0, -1)), pole=Vector((sh.x - 0.35, sh.y + 0.45, sh.z - 0.45)))
    track(t, L, 6, fr)
    apply_pose(man.o, "R", "relaxed", t); apply_pose(man.o, "R", "point", t + int(0.3 * L))
    c = cam("CAM_S05", 35, 8)
    look(c, t, Vector((-0.55, -1.55, 1.25)), Vector((0.0, 0.1, 1.05)))
    look(c, t + L, Vector((-0.42, -1.35, 1.22)), Vector((0.0, 0.12, 1.07)))
    catch(c, energy=2.0)
    mark("S05", c)

# ===================================================================== S06 CU: dead mouse on the plate in the green puddle
def S06(t, L):
    begin(ALL, t); park(t, keep=(can, plate, pud, mouse)); mouse_on_plate(t); show(can, t)
    key_matrix(can, t, Matrix.Translation(CAN_TABLE))
    base_man(man, t, MAN_XY); man.spine(t, flex=10, pitch=18)
    c = cam("CAM_S06", 60, 11); p = PLATE_P + Vector((0, 0, 0.03))
    look(c, t, p + Vector((0.20, -0.24, 0.30)), p)
    look(c, t + L, p + Vector((0.12, -0.15, 0.19)), p + Vector((0, 0, -0.005)))
    mark("S06", c)

# ===================================================================== LAB
BEAK_P = Vector((LX + 0.06, -0.12, LZ)); CANL_P = Vector((LX - 0.30, -0.18, LZ)); TRAY_P = Vector((LX + 0.32, -0.22, LZ))
def lab_base(t, liquid=0.11, with_can=True, jelly=False):
    key_obj(beaker, t, loc=BEAK_P, rot=(0, 0, 0)); show(beaker, t)
    liq.scale = (1, 1, max(0.02, liquid / 0.11)); liq.keyframe_insert("scale", frame=t)
    if liquid < 0.005: vis(liq, t, False)
    for b in bubbles: vis(b, t, liquid > 0.02)
    if with_can: key_matrix(can, t, Matrix.Translation(CANL_P) @ Matrix.Rotation(R(-30), 4, 'Z')); show(can, t)
    key_obj(tray, t, loc=TRAY_P, rot=(0, 0, 0)); show(tray, t)
    vis(jel, t, jelly)

def base_sci(t):
    vis(sci.o, t, True); base_man(sci, t, SCI_XY)

def S07(t, L):
    begin(ALL, t); park(t, keep=(beaker, liq, can, tray) + tuple(bubbles)); lab_base(t, liquid=0.0)
    base_sci(t); sci.spine(t, flex=4, pitch=-2)
    def fr(f, u):
        p = ease(min(1, u / 0.3))
        sci.spine(f, flex=4, pitch=-2 + 2 * math.sin(u * 3), turn=-6 * p, side=2 * p)
        sci.jaw(f, 2.5 * max(0, math.sin(u * 9)))
        sc.frame_set(f); sh = sci.r.PB["upperarm01.R"].head
        W = Vector((sh.x + 0.06 * p, sh.y - 0.06 - 0.20 * p, sh.z - 0.53 + 0.25 * p))
        sci.hand("R", f, W, Vector((0.05, -0.25 * (1 - p), 1)), Vector((1, 0, 0)), pole=Vector((sh.x - 0.40, sh.y + 0.30, sh.z - 0.45)))
    track(t, L, 6, fr)
    apply_pose(sci.o, "R", "relaxed", t); apply_pose(sci.o, "R", "point", t + int(0.3 * L))
    c = cam("CAM_S07", 42, 8)
    look(c, t, Vector((LX + 0.35, -1.45, 1.42)), Vector((LX - 0.02, 0.3, 1.32)))
    look(c, t + L, Vector((LX + 0.25, -1.25, 1.42)), Vector((LX - 0.02, 0.3, 1.34)))
    catch(c, energy=2.0)
    mark("S07", c)

def S08(t, L):
    """pour: can (right hand) tips over the beaker; the green stream runs while the level rises"""
    begin(ALL, t); park(t, keep=(beaker, liq, can, tray, stream) + tuple(bubbles)); lab_base(t, liquid=0.02, with_can=False)
    base_sci(t); sci.spine(t, flex=12, pitch=14)
    show(can, t); show(stream, t)
    rim = BEAK_P + Vector((-0.035, 0.0, 0.176 + 0.045))
    C0 = can_frame((-0.6, 0.0, 0.8), rim + Vector((-0.04, 0, 0.03)))
    key_matrix(can, t, C0); sc.frame_set(t)
    a = C0.to_3x3() @ Vector((0, 0, 1)); org = C0.translation
    side = C0.to_3x3() @ Vector((1, 0, 0))
    grip_object(sci.o, "R", t, can, org + a * 0.055 + Vector((0, 0.033, 0)), (0, -1, 0))
    H = Held(can, sci, "R"); H.grab(t)
    def fr(f, u):
        k = ease(min(1, u / 0.3))
        a = Vector((-0.6 - 0.3 * k, 0.0, 0.8 - 1.1 * k))
        lipp = rim + Vector((-0.04 * (1 - k), 0, 0.03 * (1 - k)))
        Cw = can_frame(a, lipp)
        sh = sci.r.PB["upperarm01.R"].head
        hand_target(sci, "R", f, H.wrist_for(Cw), pole=Vector((sh.x - 0.4, sh.y + 0.45, sh.z - 0.35)))
        sci.spine(f, flex=12 + 2 * k, pitch=14 + 4 * k, turn=-4 * k)
        lvl = 0.02 + 0.08 * ease(max(0, (u - 0.25) / 0.75))
        liq.scale = (1, 1, lvl / 0.11); liq.keyframe_insert("scale", frame=f)
        # stream: from the can lip down to the liquid surface, grows once the can is tipped
        cu = stream.data; sp = cu.splines[0]; bp = sp.bezier_points
        top = Cw @ Vector((0, 0.026, 0.122)); bot = BEAK_P + Vector((-0.005, 0, lvl + 0.004))
        if f == t:
            key_obj(stream, f, loc=(0, 0, 0))
        pts = [top, top.lerp(bot, 0.5) + Vector((0.006, 0, 0)), bot]
        for b, p_ in zip(bp, pts):
            b.co = p_; b.handle_left_type = b.handle_right_type = 'AUTO'
            b.keyframe_insert("co", frame=f); b.keyframe_insert("handle_left", frame=f); b.keyframe_insert("handle_right", frame=f)
        cu.bevel_factor_end = ease(max(0, min(1, (u - 0.22) / 0.12))); cu.keyframe_insert("bevel_factor_end", frame=f)
    track(t, L, 3, fr)
    c = cam("CAM_S08", 35, 8); catch(c, energy=2.0)
    look(c, t, BEAK_P + Vector((0.40, -1.05, 0.50)), BEAK_P + Vector((-0.10, 0.25, 0.36)))
    look(c, t + L, BEAK_P + Vector((0.30, -0.92, 0.46)), BEAK_P + Vector((-0.10, 0.25, 0.34)))
    mark("S08", c)

def S09(t, L):
    """mouse slides off the spatula blade into the beaker"""
    begin(ALL, t); park(t, keep=(beaker, liq, can, tray, spat, mouse) + tuple(bubbles)); lab_base(t, liquid=0.10)
    base_sci(t); sci.spine(t, flex=12, pitch=16)
    show(spat, t); show(mouse, t)
    tipP = BEAK_P + Vector((-0.02, 0.0, 0.176 + 0.06))
    def spat_M(tilt):
        return Matrix.Translation(tipP) @ Matrix.Rotation(R(-tilt), 4, 'Y') @ Matrix.Translation(Vector((-0.11, 0, 0)))
    S0 = spat_M(5); key_matrix(spat, t, S0); sc.frame_set(t)
    grip_object(sci.o, "R", t, spat, S0 @ Vector((-0.15, 0, 0)), (0, 0, -1), grip="wrap")
    H = Held(spat, sci, "R"); H.grab(t)
    msl = Matrix.Rotation(R(90), 4, 'Z')        # mouse lies along the blade
    def fr(f, u):
        k = ease(min(1, max(0, (u - 0.15) / 0.35)))
        Sw = spat_M(5 + 30 * k)
        sh = sci.r.PB["upperarm01.R"].head
        hand_target(sci, "R", f, H.wrist_for(Sw), pole=Vector((sh.x - 0.45, sh.y + 0.4, sh.z - 0.35)))
        sci.spine(f, flex=12, pitch=16 + 4 * k)
        # mouse: on the blade until k~0.5, then slides off the tip and drops into the liquid
        if u < 0.33:
            M = Sw @ Matrix.Translation(Vector((0.07, 0, 0.0035 + 0.019))) @ msl
        else:
            v = min(1, (u - 0.33) / 0.30)
            start = (spat_M(5 + 30 * ease(min(1, max(0, (0.33 - 0.15) / 0.35))))) @ Vector((0.07, 0, 0.022))
            end = BEAK_P + Vector((0.0, 0.0, 0.07))
            pos = start.lerp(end, v) + Vector((0.03 * math.sin(math.pi * v), 0, -0.0 + 0.02 * math.sin(math.pi * v)))
            M = Matrix.Translation(pos) @ Matrix.Rotation(R(-35 * v), 4, 'Y') @ msl
        key_matrix(mouse, f, M)
    track(t, L, 3, fr)
    c = cam("CAM_S09", 35, 8); catch(c, energy=2.0)
    look(c, t, BEAK_P + Vector((-0.45, -1.0, 0.50)), BEAK_P + Vector((0.0, 0.25, 0.34)))
    look(c, t + L, BEAK_P + Vector((-0.36, -0.88, 0.44)), BEAK_P + Vector((0.0, 0.25, 0.30)))
    mark("S09", c)

def S10(t, L):
    """macro: the mouse sinks, fizzes, shrinks and turns into a green jelly lump"""
    begin(ALL, t); park(t, keep=(beaker, liq, can, tray, mouse, jel) + tuple(bubbles)); lab_base(t, liquid=0.10)
    show(mouse, t); show(jel, t)
    base_sci(t); sci.spine(t, flex=10, pitch=18)
    random.seed(7)
    for i, b in enumerate(bubbles):
        ph = random.random(); x, y = b.location.x, b.location.y
        for j in range(0, L + 1, 6):
            z = 0.012 + ((j / L * 2.2 + ph) % 1.0) * 0.085
            b.location = (x, y, z); b.keyframe_insert("location", frame=t + j)
    def fr(f, u):
        s = 1.0 - 0.85 * ease(u)
        pos = BEAK_P + Vector((0.0, 0.0, 0.07 - 0.04 * ease(min(1, u * 2))))
        M = Matrix.Translation(pos) @ Matrix.Rotation(R(-35 - 40 * u), 4, 'Y') @ Matrix.Rotation(R(90), 4, 'Z') @ Matrix.Scale(max(0.08, s), 4)
        key_matrix(mouse, f, M)
        j = ease(max(0, (u - 0.15) / 0.85))
        key_obj(jel, f, loc=BEAK_P + Vector((0, 0, 0.012 + 0.02 * j)), rot=(0, 0, u * 2), scale=(0.75 * j + 0.001, 0.75 * j + 0.001, (0.9 + 0.1 * math.sin(u * 20)) * j + 0.001))
    track(t, L, 3, fr)
    vis(mouse, t + int(L * 0.92), False)
    c = cam("CAM_S10", 70, 11); p = BEAK_P + Vector((0, 0, 0.06))
    look(c, t, p + Vector((0.10, -0.40, 0.03)), p)
    look(c, t + L, p + Vector((0.06, -0.30, 0.02)), p + Vector((0, 0, -0.02)))
    mark("S10", c)

def S11(t, L):
    """scientist tips the beaker; the jelly lump slides out onto the steel tray"""
    begin(ALL, t); park(t, keep=(beaker, can, tray, jel)); lab_base(t, liquid=0.0, jelly=True)
    base_sci(t); sci.spine(t, flex=12, pitch=16)
    B0 = Matrix.Translation(BEAK_P) ; key_matrix(beaker, t, B0); sc.frame_set(t)
    grip_object(sci.o, "R", t, beaker, BEAK_P + Vector((-0.055, 0, 0.09)), (1, 0, 0), finger_dir=Vector((0, -1, 0)))
    H = Held(beaker, sci, "R"); H.grab(t)
    over = TRAY_P + Vector((-0.10, 0.0, 0.16))
    def BM(k):
        piv = BEAK_P.lerp(over, k)
        return Matrix.Translation(piv) @ Matrix.Rotation(R(-105 * ease(max(0, (k - 0.3) / 0.7))), 4, 'Y')
    def fr(f, u):
        k = ease(min(1, u / 0.55))
        Bw = BM(k)
        sh = sci.r.PB["upperarm01.R"].head
        hand_target(sci, "R", f, H.wrist_for(Bw), pole=Vector((sh.x - 0.45, sh.y + 0.4, sh.z - 0.4)))
        sci.spine(f, flex=12 + 4 * k, pitch=16 + 4 * k, turn=8 * k)
        sl = ease(max(0, min(1, (u - 0.42) / 0.35)))
        inside = Bw @ Vector((0, 0, 0.03))
        land = TRAY_P + Vector((0.0, 0.0, 0.004 + 0.02))
        pos = inside.lerp(land, sl)
        wob = 1 + 0.18 * math.sin(max(0, u - 0.75) * 40) * math.exp(-max(0, u - 0.75) * 9) if u > 0.75 else 1.0
        key_obj(jel, f, loc=pos, rot=(0, 0, 0.3), scale=(0.75 * (2 - wob) * (1 + 0.25 * sl), 0.75 * (1 + 0.25 * sl), 0.85 * wob))
    track(t, L, 3, fr)
    c = cam("CAM_S11", 40, 8)
    look(c, t, Vector((LX + 0.62, -1.30, 1.45)), Vector((LX + 0.10, 0.10, 1.20)))
    look(c, t + L, Vector((LX + 0.55, -1.18, 1.42)), Vector((LX + 0.14, 0.05, 1.18)))
    catch(c, energy=2.0)
    mark("S11", c)

def S12(t, L):
    begin(ALL, t); park(t, keep=(can, tray, jel)); lab_base(t, liquid=0.0, jelly=True)
    key_obj(beaker, t, loc=(0, -20, -5)); vis(beaker, t, False)
    vis(sci.o, t, False)          # nobody in this close-up: no blurred coat in the lens
    key_matrix(can, t, Matrix.Translation(TRAY_P + Vector((-0.20, 0.06, 0.0))) @ Matrix.Rotation(R(160), 4, 'Z')); show(can, t)
    base_sci(t); sci.spine(t, flex=12, pitch=20)
    for j in range(0, L + 1, 3):
        u = j / L; wob = 1 + 0.07 * math.sin(u * 18) * math.exp(-u * 1.5)
        key_obj(jel, t + j, loc=TRAY_P + Vector((0, 0, 0.024)), rot=(0, 0, 0.3), scale=(0.94 * (2 - wob), 0.94, 0.85 * wob))
    c = cam("CAM_S12", 60, 11); p = TRAY_P + Vector((-0.06, 0.02, 0.03))
    look(c, t, p + Vector((0.20, -0.30, 0.36)), p)
    look(c, t + L, p + Vector((0.12, -0.20, 0.24)), p + Vector((0.02, 0, -0.005)))
    mark("S12", c)

# ===================================================================== back in the kitchen: consumers worry
def S13(t, L):
    """man holds the can at chest height and studies it, worried"""
    begin(ALL, t); park(t, keep=(can,)); show(can, t)
    base_man(man, t, MAN_XY); man.spine(t, flex=6, pitch=16, turn=-6); man.eyes(t, pitch=14)
    C0 = Matrix.Translation(Vector((-0.10, 0.06, 1.14))) @ Matrix.Rotation(R(30), 4, 'Z')
    key_matrix(can, t, C0); sc.frame_set(t)
    grip_object(man.o, "R", t, can, C0.translation + Vector((-0.033, 0.0, 0.055)), (1, 0, 0), finger_dir=Vector((0, -1, 0)))
    H = Held(can, man, "R"); H.grab(t)
    def fr(f, u):
        rot = 30 + 60 * ease(u)
        Cw = Matrix.Translation(Vector((-0.10, 0.06 - 0.02 * u, 1.14 + 0.04 * ease(u)))) @ Matrix.Rotation(R(rot), 4, 'Z') @ Matrix.Rotation(R(-8 * math.sin(u * 3)), 4, 'X')
        sh = man.r.PB["upperarm01.R"].head
        hand_target(man, "R", f, H.wrist_for(Cw), pole=Vector((sh.x - 0.4, sh.y + 0.45, sh.z - 0.35)))
        man.spine(f, flex=6, pitch=16 - 4 * u, turn=-6 + 4 * math.sin(u * 2.5), side=3 * math.sin(u * 2))
        man.eyes(f, pitch=14 - 3 * u, yaw=2 * math.sin(u * 4))
    track(t, L, 6, fr)
    c = cam("CAM_S13", 55, 8); catch(c)
    look(c, t, Vector((0.30, -0.82, 1.50)), Vector((-0.06, 0.25, 1.36)))
    look(c, t + L, Vector((0.22, -0.66, 1.49)), Vector((-0.06, 0.25, 1.38)))
    mark("S13", c)

def S14(t, L):
    """he sets the can down and slides it away from himself"""
    begin(ALL, t); park(t, keep=(can,)); show(can, t)
    base_man(man, t, MAN_XY); man.spine(t, flex=10, pitch=16); man.eyes(t, pitch=10)
    C0 = Matrix.Translation(Vector((-0.16, 0.02, 1.02)))
    key_matrix(can, t, C0); sc.frame_set(t)
    grip_object(man.o, "R", t, can, C0.translation + Vector((-0.033, 0.0, 0.055)), (1, 0, 0), finger_dir=Vector((0, -1, 0)))
    H = Held(can, man, "R"); H.grab(t)
    down = Vector((-0.16, 0.02, TZ)); away = Vector((-0.16, -0.30, TZ))
    rel_f = None
    def fr(f, u):
        a = ease(min(1, u / 0.3)); b = ease(max(0, min(1, (u - 0.3) / 0.35)))
        P = Vector((-0.16, 0.02, 1.02)).lerp(down, a).lerp(away, b)
        sh = man.r.PB["upperarm01.R"].head
        hand_target(man, "R", f, H.wrist_for(Matrix.Translation(P)), pole=Vector((sh.x - 0.35, sh.y + 0.5, sh.z - 0.4)))
        man.spine(f, flex=10 + 10 * b, pitch=16 - 6 * b, turn=0)
        man.stand(f, MAN_XY, flex=6 * b)
    track(t, L, 3, fr)
    # release when it has slid away; the hand then comes back to the side
    fr_rel = t + int(0.68 * L)
    H.release(fr_rel)
    sc.frame_set(fr_rel)
    for j in range(int(0.68 * L) + 3, L + 1, 6):
        u = j / L; r = ease((u - 0.68) / 0.32)
        man.spine(t + j, flex=20 - 18 * r, pitch=10 - 4 * r)
        man.stand(t + j, (MAN_XY[0], MAN_XY[1] + 0.06 * r), flex=6 - 6 * r)
        man.hang("R", t + j) if r > 0.95 else None
    apply_pose(man.o, "R", "relaxed", t + L)
    c = cam("CAM_S14", 38, 8)
    look(c, t, Vector((-0.80, -1.25, 1.42)), Vector((-0.10, 0.15, 1.12)))
    look(c, t + L, Vector((-0.68, -1.12, 1.40)), Vector((-0.12, 0.10, 1.12)))
    catch(c, energy=2.0)
    mark("S14", c)

def S15(t, L):
    """looks down at his own belly, one hand on the stomach"""
    begin(ALL, t); park(t, keep=(can,)); show(can, t)
    key_matrix(can, t, Matrix.Translation(Vector((-0.16, -0.30, TZ))))
    base_man(man, t, (MAN_XY[0], MAN_XY[1] + 0.25))
    def fr(f, u):
        k = ease(min(1, u / 0.4))
        man.stand(f, (MAN_XY[0], MAN_XY[1] + 0.25), flex=4 * k)
        man.spine(f, flex=10 * k, pitch=30 * k, turn=0, side=2 * math.sin(u * 3))
        man.eyes(f, pitch=18 * k)
        sc.frame_set(f); sh = man.r.PB["upperarm01.L"].head
        belly = man.o.matrix_world @ (man.r.PB["spine04"].matrix @ man.r.rest("spine04").inverted() @ Vector((0.03, -0.17, man.r.BN["spine04"].head_local.z + 0.02)))
        if k > 0:
            place_hand(man.o, "L", f, sh.lerp(belly, 0.35 + 0.65 * k) + Vector((0, -0.03 * (1 - k), 0)), (0, 1, 0), (-1, 0, -0.25))
    track(t, L, 6, fr)
    apply_pose(man.o, "L", "relaxed", t); apply_pose(man.o, "L", "flat_palm", t + int(0.4 * L))
    c = cam("CAM_S15", 32, 8)
    look(c, t, Vector((0.22, -1.30, 1.30)), Vector((0.0, 0.67, 1.15)))
    look(c, t + L, Vector((0.12, -1.10, 1.30)), Vector((0.0, 0.67, 1.17)))
    catch(c, energy=2.0)
    mark("S15", c)

def S16(t, L):
    """final: worried CU, eyes go to the can on the table and back"""
    begin(ALL, t); park(t, keep=(can,)); show(can, t)
    key_matrix(can, t, Matrix.Translation(Vector((-0.16, -0.30, TZ))))
    base_man(man, t, MAN_XY)
    def fr(f, u):
        g = math.sin(math.pi * min(1, u / 0.55))
        man.spine(f, flex=6 + 6 * g, pitch=6 + 14 * g, turn=-14 * g, side=-2 * g)
        man.eyes(f, pitch=8 * g, yaw=-6 * g)
        man.jaw(f, 1.5 * max(0, (u - 0.6) / 0.4))
    track(t, L, 6, fr)
    c = cam("CAM_S16", 60, 8); catch(c)
    look(c, t, Vector((0.25, -0.62, 1.53)), Vector((0.0, 0.40, 1.48)))
    look(c, t + L, Vector((0.15, -0.46, 1.53)), Vector((0.0, 0.40, 1.49)))
    mark("S16", c)

for k, _ in SHOTS:
    t0, t1 = T[k]; L = CLIP[k]
    print("BUILD", k, t0, t1, L); sys.stdout.flush()
    globals()[k](t0, L)

# hard cuts: camera keys and prop vis are per-shot already; set every rig/prop key just before a cut to CONSTANT
cuts = sorted(v[0] for v in T.values())
for o in ALL + list(cams.objects):
    for fc in all_fcurves(o):
        for kp in fc.keyframe_points:
            if any(abs(kp.co.x - (c - 1)) < 0.01 for c in cuts): kp.interpolation = 'CONSTANT'
sc.camera = O["CAM_S01"]
json.dump({k: list(v) for k, v in T.items()}, open(BUILD + "/timing_used.json", "w"))
bpy.ops.wm.save_as_mainfile(filepath=BUILD + "/anim.blend")
print("ANIM saved", FEND)
