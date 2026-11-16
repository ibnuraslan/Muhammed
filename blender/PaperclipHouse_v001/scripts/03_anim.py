"""B36 PaperclipHouse: every shot as its own 1x clip (~30% longer than its beat), one camera per shot, hard cuts by markers.
blender -b build/sets.blend --python 03_anim.py [-- timing.json]
timing.json (Phase 2): {"S01": [cut_in, cut_out], ...}. Without it the clips run back to back at full length (Phase 1).
Hands follow the items (IK targets keyed to item-space grip frames found by hand_poses.grip_object / place_hand),
so a held item can never drift off the fingers; an item moves only while a hand holds it."""
import bpy, os, sys, json, math
from mathutils import Vector, Matrix
D = os.path.dirname(os.path.abspath(__file__))
exec(open(D + "/common.py").read())
exec(open(PIPE + "/anim_lib.py").read()); exec(open(PIPE + "/hand_poses.py").read()); exec(open(D + "/lib.py").read())
R = math.radians
sc = bpy.context.scene
sc.render.fps = 60; sc.render.resolution_x = 1080; sc.render.resolution_y = 1920
cams = bpy.data.collections.get("CAMS") or bpy.data.collections.new("CAMS")
if cams.name not in sc.collection.children: sc.collection.children.link(cams)
O = bpy.data.objects

# ------------------------------------------------------------------ shot table (id, expected beat seconds) in reference order
SHOTS = [("S01", 2.4), ("S02", 1.5), ("S03", 2.4), ("S04", 1.3), ("S05", 2.4), ("S06", 2.4), ("S07", 2.4), ("S08", 1.8),
         ("S09", 2.0), ("S10", 2.2), ("S11", 1.4), ("S12", 2.4), ("S13", 1.5), ("S14", 2.4), ("S15", 2.4), ("S16", 1.4),
         ("S17", 2.0), ("S18", 1.5), ("S19", 1.5), ("S20", 1.6), ("S21", 2.4), ("S22", 2.0), ("S23", 2.0), ("S24", 1.4),
         ("S25", 2.4), ("S26", 2.4), ("S27", 2.4), ("S28", 1.8), ("S29", 2.6)]
CLIP = {k: int(round(1.3 * s * 60)) for k, s in SHOTS}
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = None
if argv and argv[0].endswith(".json"):
    T = {k: tuple(v) for k, v in json.load(open(argv[0])).items()}
else:
    T = {}; f = 1
    for k, s in SHOTS: T[k] = (f, f + CLIP[k]); f += CLIP[k]
    if argv: ONLY = set(argv[0].split(","))
FEND = max(v[1] for v in T.values()) - 1
sc.frame_start = 1; sc.frame_end = FEND

NAMES = ["Hero", "PenLady", "KnobMan", "Camper", "Worker", "KegGuy", "SledGuy", "VanGuy", "Exec", "Landlady", "Rocker", "Director", "Mayor"]
class Person(Man):
    def __init__(self, n):
        super().__init__(n); self.yaw = 0.0; self.xy = (0, 0)
    def stand(self, f, xy, yaw=0.0, crouch=0.0, flex=0.0, side=0.0, stance=1.0):
        self.yaw = yaw; self.xy = xy
        super().stand(f, xy, yaw, crouch, flex, side, stance)
    def hang(self, s, f, **kw):
        sc.frame_set(f)                      # root pose of THIS frame (hang is relative to the evaluated root)
        super().hang(s, f, **kw)
    def fwd(self): return Vector((math.sin(R(self.yaw)), -math.cos(R(self.yaw)), 0))
    def right(self): return Vector((-math.cos(R(self.yaw)), -math.sin(R(self.yaw)), 0))
    def shoulder(self, s):
        return self.o.matrix_world @ self.r.PB["upperarm01." + s].head
    def head_w(self):
        return self.o.matrix_world @ self.r.PB["head"].head
M = {n: Person(n) for n in NAMES}
hero = M["Hero"]
PRC = bpy.data.collections["PROPS"]
for nm in ("P_CondoKeys",):
    for cp in ("P_VanKeys", "P_HouseKeys"):
        if cp not in O:
            c = O[nm].copy(); c.data = O[nm].data; c.name = cp; PRC.objects.link(c)
PROPS = [o for o in PRC.objects if o.parent is None]
ALLRIG = [m.o for m in M.values()]
ALL = ALLRIG + PROPS

def begin(objs, t):
    """hard cut at t: every channel of objs holds its value at t-1 (CONSTANT) and loses keys >= t-1"""
    for o in objs:
        for fc in all_fcurves(o):
            if not len(fc.keyframe_points): continue
            v = fc.evaluate(t - 1)
            while True:
                ks = [k for k in fc.keyframe_points if k.co.x >= t - 1 - 1e-3]
                if not ks: break
                fc.keyframe_points.remove(ks[-1])
            fc.update(); kp = fc.keyframe_points.insert(t - 1, v); kp.interpolation = 'CONSTANT'

def vis_obj(o, f, on):
    for ob in [o] + list(o.children_recursive):
        ob.hide_render = not on; ob.hide_viewport = not on
        ob.keyframe_insert("hide_render", frame=f); ob.keyframe_insert("hide_viewport", frame=f)

def setup(t, men, props):
    """start a shot: freeze everything, show only the given people and props"""
    begin(ALL, t)
    for m in M.values(): vis_obj(m.o, t, m in men)
    for p in PROPS:
        on = p in props
        vis_obj(p, t, on)
        key_obj(p, t, scale=(1, 1, 1))
        if not on: key_obj(p, t, loc=(300, 0, -50))

def base(m, t, xy, yaw, pose="relaxed"):
    m.stand(t, xy, yaw); m.spine(t); m.jaw(t, 0); m.eyes(t); sc.frame_set(t)
    for s in "LR": m.hang(s, t, pose=pose)

def track(t0, n, step, fn):
    for i in list(range(0, n + 1, step)) + ([n] if n % step else []):
        fn(t0 + i, i / n)

def ease(u): return smooth(max(0.0, min(1.0, u)))

def pole_for(m, s, out=0.45, back=0.30, down=0.45):
    sx = 1 if s == "L" else -1
    return m.shoulder(s) - m.right() * sx * out - m.fwd() * back + Vector((0, 0, -down))

def ik_world(m, s):
    return m.o.matrix_world @ m.r.PB["IK_hand." + s].matrix

def look_at(m, f, p, amount=1.0, extra_pitch=0.0, flex=0.0, twist=0.0, side=0.0):
    """head (and a little spine) toward world point p"""
    sc.frame_set(f)
    hd = m.head_w(); d = Vector(p) - hd
    fw = m.fwd(); rt = m.right()
    yaw = math.degrees(math.atan2(-d.dot(rt), d.dot(fw)))          # + = toward the character's left
    pitch = math.degrees(math.atan2(-d.z, max(0.05, d.to_2d().length)))   # + = looking down
    yaw = max(-55, min(55, yaw)) * amount; pitch = max(-25, min(40, pitch)) * amount
    m.spine(f, flex=flex, twist=twist + yaw * 0.25, side=side, pitch=pitch + extra_pitch, turn=yaw * 0.75)
    m.eyes(f, yaw=0, pitch=0)

def item_matrix(p, yaw_deg, tilt=None):
    Mx = Matrix.Translation(Vector(p)) @ Matrix.Rotation(R(yaw_deg), 4, 'Z')
    if tilt is not None: Mx = Mx @ tilt
    return Mx

def key_path(item, t0, n, fn, step=2):
    """fn(u) -> world 4x4 of the item; keyed every `step` frames"""
    def k(f, u): key_matrix(item, f, fn(u))
    track(t0, n, step, k)

# hand grips: spec = (person, side, local_contact, local_approach, local_finger_dir, mode) ; mode 'grip' (grip_object) or a pose name (place_hand)
BIND = []
def bind_items():
    """the holding hand drives its item: re-key the item every frame from the EVALUATED wrist (no drift off the fingers)"""
    for item, m, s, rel, fa, fb in BIND:
        for f in range(fa, fb + 1):
            sc.frame_set(f)
            W = m.o.matrix_world @ m.r.PB["wrist." + s].matrix
            key_matrix(item, f, W @ rel)
    BIND.clear()

def attach(item, fnM, t0, n, spec, u_on, u_off, reach=18, leave=20, step=2, drive=None):
    """hand follows item between u_on..u_off (fractions of the clip); hang before (reaching in over `reach` frames) and after"""
    m, s, lc, la, lf, mode = spec
    f_on = t0 + int(round(u_on * n)); f_off = t0 + int(round(u_off * n))
    if f_on - reach > t0 and u_on > 0: m.hang(s, f_on - reach)
    sc.frame_set(f_on); Mi = item.matrix_world.copy()
    C = Mi @ Vector(lc); A = (Mi.to_3x3() @ Vector(la)).normalized(); F = (Mi.to_3x3() @ Vector(lf)).normalized()
    if mode == "grip":
        grip_object(m.o, s, f_on, item, C - A * 0.018, A, finger_dir=F)
    else:
        place_hand(m.o, s, f_on, C, A, F, skin=0.014); apply_pose(m.o, s, mode, f_on)
    sc.frame_set(f_on)
    rel = Mi.inverted() @ ik_world(m, s)
    if drive is not None:
        da, db = (t0 + int(round(drive[0] * n)), t0 + int(round(drive[1] * n)))
        Wr = m.o.matrix_world @ m.r.PB["wrist." + s].matrix
        BIND.append((item, m, s, Wr.inverted() @ Mi, da, db))
    pb = m.r.PB["Pole_elbow." + s]
    def fol(f, u):
        uu = u_on + (u_off - u_on) * u
        sc.frame_set(f)
        hand_target(m, s, f, fnM(uu) @ rel, pole=pole_for(m, s))
    track(f_on, max(1, f_off - f_on), step, fol)
    if u_off < 1.0:
        # fingers keep the grip until the release frame, then open while the hand drops back to a relaxed hang
        for bn in [b for b in m.o.pose.bones if b.name.startswith("finger") and b.name.endswith("." + s)]:
            sc.frame_set(f_on); bn.keyframe_insert("rotation_quaternion", frame=f_off, group=bn.name)
        apply_pose(m.o, s, "shield", f_off + 6)
        m.hang(s, min(t0 + n, f_off + leave))

def handover(item, giver, gsides, recv, rsides, t0, n, kind="small", ys=(0.0, 0.0), tilt=None, u=(0.12, 0.36, 0.50, 0.70), lat=0.0, hold_hi=0.0):
    """item goes from giver's front to receiver's front; both hold it between u[1]..u[2] (grab .. release).
    kind small: one hand each (giver side gsides[0], receiver rsides[0]) pinching opposite ends along the handover axis.
    kind big:   two hands each on the item's two side faces. kind cup: one hand each from below (palm up)."""
    sc.frame_set(t0)
    def front(m, sides):
        sh = sum((m.shoulder(s) for s in sides), Vector()) / len(sides)
        return sh + m.fwd() * 0.27 + Vector((0, 0, -0.30 + hold_hi)) + m.right() * lat * (1 if sides == ("R",) else -1 if sides == ("L",) else 0)
    A = front(giver, gsides); B = front(recv, rsides); Mid = (A + B) / 2 + Vector((0, 0, 0.04))
    ax = (B - A); yaw = math.degrees(math.atan2(ax.y, ax.x))
    ua, ub, uc, ud = u
    def P(v):
        if v <= ua: p = A + Vector((0, 0, 0.015 * math.sin(v * 9)))
        elif v <= ub: p = A.lerp(Mid, ease((v - ua) / (ub - ua)))
        elif v <= uc: p = Mid + Vector((0, 0, 0.01 * math.sin((v - ub) * 20)))
        elif v <= ud: p = Mid.lerp(B, ease((v - uc) / (ud - uc)))
        else: p = B + Vector((0, 0, 0.05 * ease((v - ud) / (1 - ud))))
        return item_matrix(p, yaw, tilt)
    key_path(item, t0, n, P)
    half = item.get("grip_half", max(0.02, min(0.10, item.dimensions.x * 0.30)))
    if kind == "small":
        g = (giver, gsides[0], (-half, 0, 0.0), (0, 0, -1), (1, 0, 0), "grip")
        r = (recv, rsides[0], (half, 0, 0.0), (0, 0, -1), (-1, 0, 0), "grip")
        attach(item, P, t0, n, g, 0.0, uc, drive=(0.0, uc)); attach(item, P, t0, n, r, ub, 1.0, drive=(uc, 1.0))
    elif kind == "cup":
        g = (giver, gsides[0], (-half, 0, 0.0), (0, 0, 1), (1, 0, 0), "cup_hold")
        r = (recv, rsides[0], (half, 0, 0.0), (0, 0, 1), (-1, 0, 0), "cup_hold")
        attach(item, P, t0, n, g, 0.0, uc, drive=(0.0, uc)); attach(item, P, t0, n, r, ub, 1.0, drive=(uc, 1.0))
    else:   # big: side faces at local +-Y; giver at -X half, receiver at +X half
        wy = item.dimensions.y / 2; dz = item.get("side_z", 0.0); dx = item.get("side_dx", 0.07)
        for s in gsides:
            sy = 1 if s == "L" else -1           # giver faces +X: his left is +Y
            attach(item, P, t0, n, (giver, s, (-dx, sy * wy, dz), (0, -sy, 0), (0.3, 0, -1), "cup_hold"), 0.0, uc, drive=(0.0, uc) if s == "R" else None)
        for s in rsides:
            sy = -1 if s == "L" else 1           # receiver faces -X: his left is -Y
            attach(item, P, t0, n, (recv, s, (dx, sy * wy, dz), (0, -sy, 0), (-0.3, 0, -1), "cup_hold"), ub, 1.0, drive=(uc, 1.0) if s == "R" else None)
    return P

def hold(item, m, sides, t0, n, fnM, kind="small", u_on=0.0, u_off=1.0):
    """m holds item (keyed by fnM(u)) for the whole clip"""
    key_path(item, t0, n, fnM)
    half = item.get("grip_half", max(0.02, min(0.10, item.dimensions.x * 0.30)))
    if kind == "small":
        attach(item, fnM, t0, n, (m, sides[0], (-half, 0, 0), (0, 0, -1), (1, 0, 0), "grip"), u_on, u_off, drive=(u_on, u_off))
    elif kind == "cup":
        attach(item, fnM, t0, n, (m, sides[0], (0, 0, 0), (0, 0, 1), (0, -1, 0), "cup_hold"), u_on, u_off, drive=(u_on, u_off))
    else:
        wy = item.dimensions.y / 2; dz = item.get("side_z", 0.0)
        for s in sides:
            sy = 1 if s == "L" else -1
            attach(item, fnM, t0, n, (m, s, (0, sy * wy, dz), (0, -sy, 0), (0.3, 0, -1), "cup_hold"), u_on, u_off, drive=(u_on, u_off) if s == sides[0] else None)

def catch(c, d=0.06, energy=1.5):
    nm = c.name + "_Catch"
    L = O.get(nm) or bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'POINT'))
    if L.name not in cams.objects: cams.objects.link(L)
    L.data.energy = energy; L.data.shadow_soft_size = 0.02; L.parent = c; L.location = (0, d, 0); L.data.use_shadow = False

def camera(k, lens, f0, eye0, tgt0, f1, eye1, tgt1, fstop=8.0, catch_e=1.5):
    c = cam("CAM_" + k, lens, fstop); catch(c, energy=catch_e)
    look(c, f0, eye0, tgt0); look(c, f1, eye1, tgt1)
    for fc in all_fcurves(c):
        for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'
    mk = sc.timeline_markers.new(k, frame=T[k][0]); mk.camera = c
    return c

def V(*a): return Vector(a)
def idle(m, t0, n, p, amp=1.0, flex=0.0):
    """breath + small weight shift + head on point p"""
    def fr(f, u):
        look_at(m, f, p, flex=flex + 1.5 * amp * math.sin(u * 7), side=1.5 * amp * math.sin(u * 4))
    track(t0, n, 8, fr)

def pair(cx, cy, axis_deg, gap, turn):
    """two people facing each other across a point, both turned `turn` deg toward the -Y camera side"""
    a = R(axis_deg); u = Vector((math.cos(a), math.sin(a)))
    pA = (cx - u.x * gap / 2, cy - u.y * gap / 2); pB = (cx + u.x * gap / 2, cy + u.y * gap / 2)
    yA = axis_deg + 90 - turn; yB = axis_deg - 90 + turn
    return pA, yA, pB, yB

def swap_shot(k, men, A, B, itemA, itemB, cx, cy, axis=0.0, gap=0.80, turn=28, kindB="small", lens=35, side_cam=-1, cam_d=2.3,
              extra_props=(), cam_h=1.45, push=0.3):
    """A gives itemA (A.R -> B.L), B gives itemB (B.R -> A.L) at the same time; kindB big: B (both hands) -> A (both hands), itemA none"""
    t, n = T[k][0], CLIP[k]
    props = [p for p in (itemA, itemB) if p] + list(extra_props)
    setup(t, men, props)
    pA, yA, pB, yB = pair(cx, cy, axis, gap, turn)
    base(A, t, pA, yA); base(B, t, pB, yB)
    sc.frame_set(t)
    if kindB == "big":
        handover(itemB, B, ("L", "R"), A, ("L", "R"), t, n, kind="big", hold_hi=-0.10)
    else:
        if itemA: handover(itemA, A, ("R",), B, ("L",), t, n, kind="small", lat=0.10)
        if itemB: handover(itemB, B, ("R",), A, ("L",), t, n, kind=kindB, lat=0.10)
    mid = V(cx, cy, 1.15)
    def fr(f, u):
        it = (itemB or itemA)
        look_at(A, f, it.matrix_world.translation if u < 0.75 else B.head_w(), flex=4 + 3 * math.sin(u * 5))
        look_at(B, f, it.matrix_world.translation if u < 0.6 else A.head_w(), flex=4 + 2 * math.sin(u * 4))
        if u > 0.78: A.jaw(f, 2.0 * math.sin((u - 0.78) * 20) ** 2)
    track(t, n, 4, fr)
    a = R(axis); ux = Vector((math.cos(a), math.sin(a), 0)); perp = Vector((-ux.y, ux.x, 0))
    if perp.y > 0: perp = -perp                       # camera on the -Y side
    e0 = mid + perp * cam_d - ux * 0.55 * side_cam * -1 + V(0, 0, cam_h - 1.15)
    e1 = mid + perp * (cam_d - push) - ux * 0.45 * side_cam * -1 + V(0, 0, cam_h - 1.10)
    return camera(k, lens, t, e0, mid + V(0, 0, 0.05), t + n, e1, mid + V(0, 0, 0.08))

HX, HY = sc["HOME"]; OX, OY = sc["OFFICE"]; GX, GY = sc["GARAGE"]; SX, SY = sc["STUDIO"]; CX, CY = sc["CAMP"]
NX, NY = sc["SNOW"]; VX, VY = sc["VOID"]; CZ = sc["COUNTER_Z"]
P = {n: O[n] for n in [o.name for o in PROPS]}

# ===================================================================== HOME
def S01(t, n):
    """paperclip <-> fish pen across the kitchen counter (hero behind the counter faces camera)"""
    setup(t, [hero, M["PenLady"]], [P["P_Paperclip"], P["P_FishPen"]])
    base(hero, t, (HX + 0.0, HY + 0.82), 0); base(M["PenLady"], t, (HX + 0.05, HY - 0.12), 180)
    A, B = hero, M["PenLady"]
    handover(P["P_Paperclip"], A, ("R",), B, ("L",), t, n, kind="small", lat=0.12, hold_hi=0.10)
    handover(P["P_FishPen"], B, ("R",), A, ("L",), t, n, kind="small", lat=0.12, hold_hi=0.10)
    def fr(f, u):
        look_at(A, f, P["P_FishPen"].matrix_world.translation, flex=10 + 2 * math.sin(u * 5))
        look_at(B, f, P["P_Paperclip"].matrix_world.translation, flex=10)
        A.stand(f, (HX, HY + 0.82), 0, flex=5); B.stand(f, (HX + 0.05, HY - 0.12), 180, flex=5)
    track(t, n, 4, fr)
    camera("S01", 32, t, V(HX - 1.55, HY - 1.45, 1.62), V(HX + 0.0, HY + 0.40, 1.20), t + n, V(HX - 1.30, HY - 1.20, 1.58), V(HX + 0.0, HY + 0.45, 1.22))

def S02(t, n):
    """CU: hero turns the fish pen in his fingers and smiles"""
    setup(t, [hero], [P["P_FishPen"]])
    base(hero, t, (HX, HY + 0.82), 0)
    sc.frame_set(t)
    c0 = hero.shoulder("R") + V(0.06, -0.33, -0.08)
    def fnM(u): return item_matrix(c0 + V(0.03 * ease(u), 0, 0.05 * ease(u)), 150 + 40 * ease(u), Matrix.Rotation(R(-12 * math.sin(u * 3)), 4, 'X'))
    hold(P["P_FishPen"], hero, ("R",), t, n, fnM)
    def fr(f, u):
        look_at(hero, f, P["P_FishPen"].matrix_world.translation, flex=4)
        hero.jaw(f, 2.5 * ease(u))
    track(t, n, 4, fr)
    sc.frame_set(t + n // 2); hd = hero.head_w(); pen = P["P_FishPen"].matrix_world.translation
    tg = (hd + pen) / 2
    camera("S02", 40, t, tg + V(-0.35, -1.30, 0.02), tg, t + n, tg + V(-0.28, -1.10, 0.02), tg + V(0, 0, 0.01), fstop=9)

# ===================================================================== OFFICE
def S03(t, n):
    swap_shot("S03", [hero, M["KnobMan"]], hero, M["KnobMan"], P["P_FishPen"], P["P_Doorknob"], OX, OY - 0.35, gap=0.80)

def S04(t, n):
    setup(t, [hero], [P["P_Doorknob"]])
    xy = (OX - 0.3, OY - 0.4); base(hero, t, xy, 20)
    sc.frame_set(t); c0 = hero.shoulder("L") + hero.fwd() * 0.34 + V(0, 0, -0.18)
    def fnM(u): return item_matrix(c0 + V(0, 0, 0.08 * ease(u)), 110 + 40 * ease(u))
    hold(P["P_Doorknob"], hero, ("L",), t, n, fnM)
    def fr(f, u): look_at(hero, f, P["P_Doorknob"].matrix_world.translation, flex=3); hero.jaw(f, 2 * ease(u))
    track(t, n, 4, fr)
    sc.frame_set(t + n // 2); tg = (hero.head_w() + P["P_Doorknob"].matrix_world.translation) / 2
    camera("S04", 50, t, tg + V(0.35, -1.05, 0.02), tg, t + n, tg + V(0.28, -0.85, 0.0), tg, fstop=9)

# ===================================================================== CAMP / STREET / GARAGE (big items)
def S05(t, n):
    swap_shot("S05", [hero, M["Camper"]], hero, M["Camper"], None, P["P_CampStove"], CX - 0.2, CY - 2.2, gap=0.85, kindB="big",
              extra_props=[P["P_Doorknob"]])
    key_obj(P["P_Doorknob"], t, loc=(CX + 0.30, CY + 0.62, 0.785), rot=(R(-90), 0, 0))

def S06(t, n):
    gx, gy = 51.5, -9.4
    swap_shot("S06", [hero, M["Worker"]], hero, M["Worker"], None, P["P_Generator"], gx, gy, gap=0.85, kindB="big",
              extra_props=[P["P_CampStove"]])
    key_obj(P["P_CampStove"], t, loc=(gx + 1.15, gy - 0.2, P["P_CampStove"].get("bottom_z", 0.05)), rot=(0, 0, R(20)))

def S07(t, n):
    swap_shot("S07", [hero, M["KegGuy"]], hero, M["KegGuy"], None, P["P_Keg"], GX - 0.3, GY - 0.6, gap=0.85, kindB="big",
              extra_props=[P["P_Generator"]])
    key_obj(P["P_Generator"], t, loc=(GX + 0.85, GY - 0.1, P["P_Generator"].get("bottom_z", 0.39)), rot=(0, 0, R(-30)))

def S08(t, n):
    """keg party: hero and KegGuy cheer, guests (Camper, Worker) dance; keg on the party table"""
    men = [hero, M["KegGuy"], M["Camper"], M["Worker"]]
    setup(t, men, [P["P_Keg"]])
    key_obj(P["P_Keg"], t, loc=(GX + 0.9, GY + 1.2, 0.72 + P["P_Keg"].get("bottom_z", 0.405)), rot=(0, 0, 0))
    spots = {hero: ((GX - 0.35, GY - 0.3), 15), M["KegGuy"]: ((GX + 0.45, GY - 0.1), -25), M["Camper"]: ((GX - 1.5, GY + 0.9), 35), M["Worker"]: ((GX + 1.6, GY + 0.2), -40)}
    for m, (xy, yw) in spots.items(): base(m, t, xy, yw)
    def fr(f, u):
        for i, (m, (xy, yw)) in enumerate(spots.items()):
            ph = u * 14 + i * 1.3; b = math.sin(ph)
            m.stand(f, xy, yw + 6 * math.sin(ph * 0.5), crouch=0.03 + 0.03 * (1 + b) / 2, side=3 * b)
            m.spine(f, flex=3, side=4 * b, twist=6 * math.sin(ph * 0.5), pitch=-6, turn=8 * math.sin(ph * 0.5))
            sc.frame_set(f)
            for s in "LR":
                sx = 1 if s == "L" else -1
                up = 1.0 if (m in (hero, M["KegGuy"])) else (0.55 + 0.45 * math.sin(ph + (0 if s == "L" else 1.5)))
                sh = m.shoulder(s)
                Wp = sh + m.right() * (-sx) * 0.22 + m.fwd() * 0.12 + V(0, 0, 0.30 * up + 0.08 * math.sin(ph * 2 + sx))
                m.hand(s, f, Wp, V(0, 0, 1) + m.fwd() * 0.2, m.fwd(), pole=sh - m.right() * sx * 0.5 + V(0, 0, -0.3) - m.fwd() * 0.2)
        for m in men: m.jaw(f, 3 + 2 * math.sin(u * 20))
    track(t, n, 3, fr)
    for m in men:
        for s in "LR": apply_pose(m.o, s, "power_fist" if m in (hero, M["KegGuy"]) else "relaxed", t)
    camera("S08", 26, t, V(GX - 0.6, GY - 3.2, 1.55), V(GX + 0.1, GY + 0.5, 1.45), t + n, V(GX - 0.2, GY - 2.8, 1.40), V(GX + 0.1, GY + 0.5, 1.50))

def S09(t, n):
    """garage: SledGuy presents the snowmobile with an open palm; hero steps toward it, both fists up"""
    men = [hero, M["SledGuy"]]; sm = P["P_Snowmobile"]
    setup(t, men, [sm])
    key_obj(sm, t, loc=(GX + 0.9, GY + 0.8, 0), rot=(0, 0, R(-70)))
    base(M["SledGuy"], t, (GX + 0.95, GY - 0.75), -20); base(hero, t, (GX - 1.1, GY - 0.6), 40)
    def fr(f, u):
        s_ = M["SledGuy"]; a = ease(u / 0.35)
        sc.frame_set(f); sh = s_.shoulder("L")
        s_.hand("L", f, sh + s_.fwd() * 0.30 + s_.right() * (-0.25) + V(0, 0, -0.22 + 0.10 * a), s_.fwd() * 0.6 - s_.right() * 0.8, V(0, 0, -1) * 0 + V(0, 0, 1) * 0.0 - s_.right() * 0.0 + V(0, 0, 0.0) + s_.fwd() * 0.0 + V(0, 0, 1), pole=sh - s_.right() * (-1) * 0.4 + V(0, 0, -0.4))
        look_at(s_, f, hero.head_w(), flex=3)
        w = ease((u - 0.25) / 0.4)
        hero.stand(f, (GX - 1.1 + 0.35 * w, GY - 0.6 + 0.2 * w), 40 + 10 * w)
        sc.frame_set(f)
        for s in "LR":
            sx = 1 if s == "L" else -1; sh2 = hero.shoulder(s); up = ease((u - 0.5) / 0.25)
            if u > 0.5:
                hero.hand(s, f, sh2 - hero.right() * sx * 0.20 + hero.fwd() * 0.12 + V(0, 0, -0.35 + 0.65 * up), V(0, 0, 1) * up + V(0, 0, -1) * (1 - up) + hero.fwd() * 0.3, hero.fwd(),
                          pole=sh2 - hero.right() * sx * 0.5 + V(0, 0, -0.3) - hero.fwd() * 0.2)
        look_at(hero, f, sm.matrix_world.translation + V(0, 0, 0.8), flex=2)
        hero.jaw(f, 3 * ease((u - 0.6) / 0.2))
    track(t, n, 3, fr)
    hero.hang("L", t + int(0.5 * n) - 1); hero.hang("R", t + int(0.5 * n) - 1)
    apply_pose(M["SledGuy"].o, "L", "flat_palm", t)
    for s in "LR": apply_pose(hero.o, s, "relaxed", t + int(0.5 * n)); apply_pose(hero.o, s, "power_fist", t + int(0.75 * n))
    camera("S09", 24, t, V(GX - 0.4, GY - 4.4, 1.45), V(GX - 0.05, GY + 0.2, 1.0), t + n, V(GX - 0.2, GY - 3.9, 1.40), V(GX - 0.05, GY + 0.2, 1.05))

# ===================================================================== SNOW
def S10(t, n):
    """snow trail, mountains: hero walks toward camera past the parked snowmobile, arms swinging"""
    setup(t, [hero], [P["P_Snowmobile"]])
    key_obj(P["P_Snowmobile"], t, loc=(NX + 1.2, NY + 6.0, 0), rot=(0, 0, R(160)))
    y0, y1 = NY + 7.5, NY + 4.0
    path = lambda f: Vector((NX - 0.3, y0 + (y1 - y0) * ease((f - t) / n), 0))
    base(hero, t, (NX - 0.3, y0), 0)
    hero.h.walk(path, lambda f: 0.0, t, t + n, stride=0.70)
    def fr(f, u):
        cyc = (path(f) - path(t)).length / 0.70
        for s in "LR":
            ph = math.sin(2 * math.pi * cyc + (0 if s == "L" else math.pi))
            hero.hang(s, f, fwd=0.14 * ph, lift=0.04 * max(0, ph))
        hero.eyes(f)
    track(t, n, 2, fr)
    camera("S10", 35, t, V(NX + 0.7, NY + 1.4, 1.30), V(NX - 0.3, NY + 7.0, 1.35), t + n, V(NX + 0.6, NY + 0.9, 1.30), V(NX - 0.3, NY + 4.5, 1.25))

def S11(t, n):
    """CU: hero holds up the red ticket (the trip across Canada), smiles"""
    setup(t, [hero], [P["P_TicketCard"]])
    xy = (NX - 0.3, NY + 4.0); base(hero, t, xy, 0)
    sc.frame_set(t); c0 = hero.shoulder("R") + V(0.08, -0.32, -0.16)
    def fnM(u): return item_matrix(c0 + V(0, 0, 0.07 * ease(u)), 0, Matrix.Rotation(R(70), 4, 'X'))
    P["P_TicketCard"]["grip_half"] = 0.055
    hold(P["P_TicketCard"], hero, ("R",), t, n, fnM)
    def fr(f, u): look_at(hero, f, P["P_TicketCard"].matrix_world.translation, flex=2); hero.jaw(f, 2.5 * ease(u))
    track(t, n, 4, fr)
    sc.frame_set(t + n // 2); tg = (hero.head_w() * 0.6 + P["P_TicketCard"].matrix_world.translation * 0.4)
    camera("S11", 45, t, tg + V(0.1, -1.25, 0.05), tg, t + n, tg + V(0.05, -1.0, 0.03), tg, fstop=9)

def S12(t, n):
    van = P["P_Van"]
    P["P_VanKeys"]["grip_half"] = 0.02
    swap_shot("S12", [hero, M["VanGuy"]], hero, M["VanGuy"], P["P_TicketCard"], P["P_VanKeys"], NX - 0.2, NY + 0.4, gap=0.80,
              extra_props=[van], cam_d=2.6)
    key_obj(van, t, loc=(NX + 1.2, NY + 4.6, 0), rot=(0, 0, 0))

def S13(t, n):
    """hero lays his left hand flat on the van side (logo side to camera), then turns to camera and grins"""
    van = P["P_Van"]
    setup(t, [hero], [van])
    key_obj(van, t, loc=(NX + 0.4, NY + 3.0, 0), rot=(0, 0, R(90)))
    sc.frame_set(t)
    ys = [(van.matrix_world @ Vector(c)).y for c in van.bound_box]
    side_y = min(ys) + 0.10                                     # body side panel (mirrors/wheels stick out ~10 cm)
    for c in van.children:
        if c.name.startswith("Logo_Van"):
            w = c.matrix_world.translation
            if w.y < NY + 3.0: side_y = w.y - 0.012
    xy = (NX - 1.25, side_y - 0.42); base(hero, t, xy, 60)
    def fr(f, u):
        a = ease((u - 0.12) / 0.3)
        sc.frame_set(f); sh = hero.shoulder("L")
        W1 = V(sh.x + 0.10, side_y - 0.040, sh.z - 0.30)
        W0 = sh + hero.fwd() * 0.10 + V(0, 0, -0.50)
        if u > 0.12:
            hero.hand("L", f, W0.lerp(W1, a), V(0.35, 0, 1).normalized(), V(0, 1, 0), pole=sh + V(-0.1, -0.35, -0.45))
        look_at(hero, f, V(sh.x + 0.1, side_y, 1.2) if u < 0.45 else V(NX - 0.6, NY - 2.6, 1.45), flex=1)
        hero.jaw(f, 3 * ease((u - 0.55) / 0.2))
    track(t, n, 3, fr)
    apply_pose(hero.o, "L", "flat_palm", t + int(0.42 * n))
    camera("S13", 28, t, V(NX - 0.9, NY - 2.9, 1.35), V(NX - 0.3, NY + 2.0, 1.10), t + n, V(NX - 0.95, NY - 2.4, 1.35), V(NX - 0.6, NY + 2.0, 1.15))

# ===================================================================== STUDIO
def S14(t, n):
    P["P_Contract"]["grip_half"] = 0.09
    swap_shot("S14", [hero, M["Exec"]], hero, M["Exec"], P["P_VanKeys"], P["P_Contract"], SX - 4.0, SY - 0.15, gap=0.80)

# ===================================================================== STREET condo
def S15(t, n):
    P["P_CondoKeys"]["grip_half"] = 0.02
    swap_shot("S15", [hero, M["Landlady"]], hero, M["Landlady"], P["P_Contract"], P["P_CondoKeys"], 21.0, -8.6, gap=0.80, cam_d=2.5)

def S16(t, n):
    setup(t, [hero], [P["P_CondoKeys"]])
    xy = (21.0, -8.8); base(hero, t, xy, 0)
    sc.frame_set(t); c0 = hero.shoulder("R") + V(0.06, -0.32, -0.14)
    def fnM(u): return item_matrix(c0 + V(0, 0, 0.14 * ease(u / 0.5)), 90 + 20 * math.sin(u * 6))
    hold(P["P_CondoKeys"], hero, ("R",), t, n, fnM)
    def fr(f, u): look_at(hero, f, P["P_CondoKeys"].matrix_world.translation if u < 0.5 else V(21.4, -11.9, 1.5), flex=1); hero.jaw(f, 3 * ease((u - 0.4) / 0.4))
    track(t, n, 4, fr)
    camera("S16", 30, t, V(21.6, -11.9, 1.30), V(21.0, -7.8, 1.6), t + n, V(21.5, -11.4, 1.30), V(21.0, -7.8, 1.65))

# ===================================================================== STUDIO bar: rocker, snow globe
def S17(t, n):
    P["P_CondoKeys"]["grip_half"] = 0.02
    swap_shot("S17", [hero, M["Rocker"]], hero, M["Rocker"], P["P_CondoKeys"], None, SX + 0.2, SY + 0.8, gap=0.80, extra_props=[P["P_Guitar"]])
    key_obj(P["P_Guitar"], t, loc=(SX + 1.45, SY + 1.85, 0.55), rot=(R(-12), 0, R(10)))

def S18(t, n):
    """high five: palms meet above head height"""
    men = [hero, M["Rocker"]]; setup(t, men, [P["P_Guitar"]])
    key_obj(P["P_Guitar"], t, loc=(SX + 1.45, SY + 1.85, 0.55), rot=(R(-12), 0, R(10)))
    pA, yA, pB, yB = pair(SX + 0.2, SY + 0.8, 0, 0.95, 25)
    base(hero, t, pA, yA); base(M["Rocker"], t, pB, yB)
    sc.frame_set(t)
    meet = (hero.shoulder("R") + M["Rocker"].shoulder("R")) / 2 + V(0, -0.05, 0.42)
    def fr(f, u):
        a = ease(u / 0.38); b = ease((u - 0.55) / 0.3)
        for m, s, sg in ((hero, "R", 1), (M["Rocker"], "R", -1)):
            sc.frame_set(f); sh = m.shoulder(s)
            hit = meet + V(-sg * 0.013, 0, 0)
            start = sh + m.fwd() * 0.15 + V(0, 0, -0.45)
            W = start.lerp(hit, a)
            if u > 0.55: W = hit.lerp(sh + m.fwd() * 0.2 + V(0, 0, 0.05), b)
            m.hand(s, f, W - V(sg * 0.06, 0, 0.06), V(0, 0, 1), V(sg, 0, 0), pole=sh - m.right() * (-1) * 0.45 + V(0, 0, -0.35))
            look_at(m, f, meet if u < 0.6 else (M["Rocker"] if m is hero else hero).head_w(), flex=2)
            m.jaw(f, 3 * ease((u - 0.4) / 0.2))
    track(t, n, 2, fr)
    for m in men: apply_pose(m.o, "R", "flat_palm", t)
    sc.frame_set(t); mid = (hero.head_w() + M["Rocker"].head_w()) / 2
    camera("S18", 30, t, mid + V(-0.2, -2.0, -0.05), mid + V(0, 0, -0.05), t + n, mid + V(-0.1, -1.7, -0.05), mid + V(0, 0, 0.0))

def S19(t, n):
    """rocker hands over the band snow globe (cupped from below), CU"""
    P["P_SnowGlobe"]["grip_half"] = 0.0
    men = [hero, M["Rocker"]]; setup(t, men, [P["P_SnowGlobe"]])
    pA, yA, pB, yB = pair(SX + 0.2, SY + 0.8, 0, 0.95, 25)
    base(hero, t, pA, yA); base(M["Rocker"], t, pB, yB)
    sc.frame_set(t)
    PP = handover(P["P_SnowGlobe"], M["Rocker"], ("R",), hero, ("L",), t, n, kind="cup", lat=0.0, hold_hi=0.08)
    def fr(f, u):
        look_at(hero, f, P["P_SnowGlobe"].matrix_world.translation, flex=5)
        look_at(M["Rocker"], f, P["P_SnowGlobe"].matrix_world.translation if u < 0.5 else hero.head_w(), flex=5)
        hero.jaw(f, 2.5 * ease((u - 0.6) / 0.3))
    track(t, n, 4, fr)
    sc.frame_set(t + n // 2); g = P["P_SnowGlobe"].matrix_world.translation
    hm = (hero.head_w() + M["Rocker"].head_w()) / 2; tg = hm * 0.5 + g * 0.5
    camera("S19", 32, t, tg + V(0.0, -1.75, 0.10), tg, t + n, tg + V(0.0, -1.55, 0.10), tg + V(0, 0, 0.02), fstop=9)

def S20(t, n):
    """hero holds the snow globe in both hands and looks into it"""
    setup(t, [hero], [P["P_SnowGlobe"]])
    xy = (SX + 2.4, SY + 0.6); base(hero, t, xy, -15)
    sc.frame_set(t); c0 = hero.shoulder("R") + hero.fwd() * 0.32 + hero.right() * -0.10 + V(0, 0, -0.26)
    def fnM(u): return item_matrix(c0 + V(0, 0, 0.10 * ease(u)), -15 + 25 * ease(u))
    key_path(P["P_SnowGlobe"], t, n, fnM)
    attach(P["P_SnowGlobe"], fnM, t, n, (hero, "R", (0.0, 0.0, 0.0), (0, 0, 1), (0, -1, 0.0), "cup_hold"), 0.0, 1.0, drive=(0.0, 1.0))
    def fr(f, u): look_at(hero, f, P["P_SnowGlobe"].matrix_world.translation + V(0, 0, 0.06), flex=3); hero.jaw(f, 2 * ease(u))
    track(t, n, 4, fr)
    sc.frame_set(t + n // 2); tg = hero.head_w() * 0.5 + P["P_SnowGlobe"].matrix_world.translation * 0.5
    camera("S20", 42, t, tg + V(-0.25, -1.15, -0.05), tg, t + n, tg + V(-0.15, -0.95, -0.03), tg, fstop=9)

def S21(t, n):
    P["P_SnowGlobe"]["grip_half"] = 0.0; P["P_Clapper"]["grip_half"] = 0.10
    men = [hero, M["Director"]]
    t_ = T["S21"][0]
    swap_shot("S21", men, hero, M["Director"], None, P["P_Clapper"], SX + 3.9, SY + 0.2, gap=0.80, extra_props=[P["P_SnowGlobe"], P["P_MovieCamera"]])
    # the globe: hero hands it over at the same time (cupped, his R -> director's L)
    PP = handover(P["P_SnowGlobe"], hero, ("R",), M["Director"], ("L",), t_, n, kind="cup", lat=0.10, hold_hi=0.0)
    key_obj(P["P_MovieCamera"], t_, loc=(SX + 5.0, SY + 0.9, 0), rot=(0, 0, R(120)))

def S22(t, n):
    """film set: director (clapper raised) cues; hero acts in the lights, arms open"""
    men = [hero, M["Director"]]; setup(t, men, [P["P_Clapper"], P["P_MovieCamera"]])
    key_obj(P["P_MovieCamera"], t, loc=(SX + 3.2, SY - 0.4, 0), rot=(0, 0, R(-120)))
    base(hero, t, (SX + 4.5, SY + 1.2), -30); base(M["Director"], t, (SX + 2.7, SY + 0.2), -110)
    sc.frame_set(t); d = M["Director"]; c0 = d.shoulder("R") + d.fwd() * 0.30 + V(0, 0, -0.05)
    def fnM(u): return item_matrix(c0 + V(0, 0, 0.12 * math.sin(math.pi * ease(u / 0.5))), d.yaw + 90)
    hold(P["P_Clapper"], d, ("R",), t, n, fnM)
    def fr(f, u):
        look_at(d, f, hero.head_w(), flex=2)
        a = ease((u - 0.3) / 0.35); sc.frame_set(f)
        for s in "LR":
            sx = 1 if s == "L" else -1; sh = hero.shoulder(s)
            W = (sh + hero.right() * (-sx) * 0.10 + V(0, 0, -0.50)).lerp(sh - hero.right() * sx * 0.22 + hero.fwd() * 0.30 + V(0, 0, -0.42), a)
            hero.hand(s, f, W, (W - sh).normalized(), hero.fwd(), pole=sh - hero.right() * sx * 0.3 + V(0, 0, -0.4) - hero.fwd() * 0.2)
        look_at(hero, f, P["P_MovieCamera"].matrix_world.translation + V(0, 0, 1.4), flex=-3)
        hero.jaw(f, 3 * a)
    track(t, n, 3, fr)
    for s in "LR": apply_pose(hero.o, s, "open_alarm", t)
    camera("S22", 26, t, V(SX + 3.1, SY - 2.4, 1.6), V(SX + 3.8, SY + 0.8, 1.2), t + n, V(SX + 3.3, SY - 2.0, 1.55), V(SX + 3.9, SY + 0.8, 1.25))

# ===================================================================== STREET: newspaper readers
def S23(t, n):
    m = M["Mayor"]; np_ = P["P_Newspaper"]
    men = [m, M["PenLady"]]; setup(t, men, [np_])
    base(m, t, (-1.5, -11.0), 15); base(M["PenLady"], t, (-0.4, -10.4), -30)
    sc.frame_set(t); c0 = (m.shoulder("L") + m.shoulder("R")) / 2 + m.fwd() * 0.40 + V(0, 0, -0.22)
    def fnM(u): return item_matrix(c0 + V(0, 0, 0.02 * math.sin(u * 4)), m.yaw, Matrix.Rotation(R(-15), 4, 'X') @ Matrix.Translation(V(0.22, 0, 0)))
    key_path(np_, t, n, fnM)
    for s, x in (("L", 0.20), ("R", -0.20)):
        attach(np_, fnM, t, n, (m, s, (x * 1.0 - 0.0, 0.0, 0.10), (0, 1, 0), (0, 0, -1), "grip"), 0.0, 1.0, drive=(0.0, 1.0) if s == "L" else None)
    def fr(f, u):
        look_at(m, f, np_.matrix_world.translation + V(0, 0, 0.05), flex=4)
        look_at(M["PenLady"], f, np_.matrix_world.translation, flex=6)
        M["PenLady"].jaw(f, 2 * ease(u))
    track(t, n, 4, fr)
    camera("S23", 30, t, V(-0.6, -13.6, 1.45), V(-1.0, -10.6, 1.35), t + n, V(-0.7, -13.2, 1.45), V(-1.0, -10.6, 1.40))

# ===================================================================== VOID: hero with the paperclip; the chain of trades
def S24(t, n):
    setup(t, [hero], [P["P_Paperclip"]])
    base(hero, t, (VX, VY), 0)
    sc.frame_set(t); c0 = hero.shoulder("R") + V(0.08, -0.32, -0.14)
    P["P_Paperclip"]["grip_half"] = 0.012
    def fnM(u): return item_matrix(c0 + V(0.0, 0, 0.06 * ease(u)), 0, Matrix.Rotation(R(75), 4, 'X'))
    hold(P["P_Paperclip"], hero, ("R",), t, n, fnM)
    def fr(f, u): look_at(hero, f, P["P_Paperclip"].matrix_world.translation if u < 0.45 else V(VX - 0.3, VY - 3, 1.6), flex=1); hero.jaw(f, 2.5 * ease((u - 0.4) / 0.4))
    track(t, n, 4, fr)
    sc.frame_set(t + n // 2); tg = hero.head_w() * 0.55 + P["P_Paperclip"].matrix_world.translation * 0.45
    camera("S24", 40, t, tg + V(-0.2, -1.35, 0.0), tg, t + n, tg + V(-0.15, -1.1, 0.0), tg, fstop=9)

CHAIN = ["P_Paperclip", "P_FishPen", "P_Doorknob", "P_CampStove", "P_Generator", "P_Keg", "P_Snowmobile", "P_TicketCard", "P_Van",
         "P_Contract", "P_CondoKeys", "P_SnowGlobe", "P_Clapper"]
def S25(t, n):
    """explainer: every traded item stands on a line on the bright sky stage, small to big; camera tracks along the chain"""
    items = [P[k] for k in CHAIN]
    setup(t, [], items)
    for o in items:
        for c in o.children:
            if c.name.startswith("Logo_"): vis_obj(c, t, False)
    x = VX - 3.0; size = 0.55; gap = 0.85
    for i, (k, o) in enumerate(zip(CHAIN, items)):
        d = o.dimensions; s_ = size / max(d.x, d.y, d.z)
        x = VX - 3.0 + i * gap
        key_obj(o, t, loc=(x, VY + 1.0, 0.95), rot=(R(12), 0, R(25)), scale=(s_, s_, s_))
        key_obj(o, t + n, loc=(x, VY + 1.0, 0.95), rot=(R(12), 0, R(55)), scale=(s_, s_, s_))
    for o in items: key_obj(o, T["S25"][1], scale=(1, 1, 1))
    camera("S25", 35, t, V(VX - 2.2, VY - 2.3, 1.25), V(VX - 2.0, VY + 1.0, 0.95), t + n, V(x - 0.8, VY - 2.3, 1.25), V(x - 0.6, VY + 1.0, 0.95), fstop=11)

# ===================================================================== STREET: one year later, the house
def S26(t, n):
    """hero walks up the sidewalk past the blue mailbox toward the house"""
    setup(t, [hero], [])
    x = 1.5; y0, y1 = -6.8, -9.6
    path = lambda f: Vector((x, y0 + (y1 - y0) * ease((f - t) / n), 0))
    base(hero, t, (x, y0), 0)
    hero.h.walk(path, lambda f: 0.0, t, t + n, stride=0.70)
    def fr(f, u):
        cyc = (path(f) - path(t)).length / 0.70
        for s in "LR":
            ph = math.sin(2 * math.pi * cyc + (0 if s == "L" else math.pi))
            hero.hang(s, f, fwd=0.14 * ph, lift=0.04 * max(0, ph))
        look_at(hero, f, V(3.0, -10.6, 1.0) if u > 0.5 else V(4.0, -14.0, 1.5), amount=0.6)
    track(t, n, 2, fr)
    camera("S26", 30, t, V(0.4, -14.4, 1.25), V(1.7, -7.5, 1.35), t + n, V(0.5, -14.0, 1.25), V(1.8, -9.0, 1.25))

def S27(t, n):
    P["P_Clapper"]["grip_half"] = 0.10; P["P_HouseKeys"]["grip_half"] = 0.02
    swap_shot("S27", [hero, M["Mayor"]], hero, M["Mayor"], P["P_Clapper"], P["P_HouseKeys"], 0.0, -6.6, gap=0.80, cam_d=2.6)

def S28(t, n):
    """house reveal: hero in front of his house, both arms up; camera cranes up and back"""
    setup(t, [hero], [P["P_HouseKeys"]])
    xy = (0.0, -7.2); base(hero, t, xy, 180)
    sc.frame_set(t)
    def fnM(u):
        sc_ = hero.shoulder("R"); return item_matrix(sc_ + V(-0.02, 0.0, -0.55), 0)
    key_obj(P["P_HouseKeys"], t, loc=(300, 0, -50)); vis_obj(P["P_HouseKeys"], t, False)
    def fr(f, u):
        a = ease((u - 0.25) / 0.3); sc.frame_set(f)
        for s in "LR":
            sx = 1 if s == "L" else -1; sh = hero.shoulder(s)
            W = (sh + hero.right() * (-sx) * 0.12 + V(0, 0, -0.5)).lerp(sh - hero.right() * sx * 0.25 + V(0, 0.05, 0.55), a)
            hero.hand(s, f, W, (W - sh).normalized(), hero.fwd() * -1 * 0 + V(0, 1, 0), pole=sh - hero.right() * sx * 0.4 + V(0, 0, -0.3) + V(0, 0.2, 0))
        look_at(hero, f, V(0, 0, 4.5), flex=-4)
    track(t, n, 3, fr)
    for s in "LR": apply_pose(hero.o, s, "power_fist", t + int(0.4 * n))
    camera("S28", 24, t, V(0.9, -10.6, 1.2), V(0.0, -3.0, 2.4), t + n, V(1.4, -13.0, 2.2), V(0.0, -2.0, 2.9))

def S29(t, n):
    """inside his new home: hero walks in, stops in the living room, looks around, smiles; camera pushes in"""
    setup(t, [hero], [])
    x = HX + 1.28; y0, y1 = HY + 1.9, HY + 0.5
    path = lambda f: Vector((x, y0 + (y1 - y0) * ease((f - t) / (0.6 * n)), 0))
    base(hero, t, (x, y0), 0)
    hero.h.walk(path, lambda f: 0.0, t, t + int(0.6 * n), stride=0.65)
    def fr(f, u):
        cyc = (path(f) - path(t)).length / 0.65
        for s in "LR":
            ph = math.sin(2 * math.pi * cyc + (0 if s == "L" else math.pi)) if u < 0.6 else 0.0
            hero.hang(s, f, fwd=0.12 * ph, lift=0.03 * max(0, ph))
        look_at(hero, f, V(HX - 2.5 + 3.5 * ease((u - 0.55) / 0.45), HY - 1.5, 1.6) if u > 0.55 else V(HX + 1.0, HY - 3.0, 1.6), amount=0.8)
        hero.jaw(f, 2.5 * ease((u - 0.6) / 0.3))
    track(t, n, 2, fr)
    camera("S29", 30, t, V(HX + 0.3, HY - 2.6, 1.55), V(HX + 1.1, HY + 1.4, 1.3), t + n, V(HX + 0.5, HY - 2.2, 1.55), V(HX + 1.15, HY + 0.6, 1.4))

for k, _ in SHOTS:
    if ONLY and k not in ONLY: continue
    t0, t1 = T[k]; L = CLIP[k]
    print("BUILD", k, t0, t1, L); sys.stdout.flush()
    globals()[k](t0, L)
    bind_items()

cuts = sorted(v[0] for v in T.values())
for o in ALL + list(cams.objects):
    for fc in all_fcurves(o):
        for kp in fc.keyframe_points:
            if any(abs(kp.co.x - (c - 1)) < 0.01 for c in cuts): kp.interpolation = 'CONSTANT'
sc.camera = O["CAM_" + (sorted(ONLY)[0] if ONLY else "S01")]
json.dump({k: list(v) for k, v in T.items()}, open(BUILD + "/timing_used.json", "w"))
bpy.ops.wm.save_as_mainfile(filepath=BUILD + "/anim.blend")
print("ANIM saved", FEND)
