"""All shots as 1x clips (each ~30% longer than its expected beat), one camera per shot, hard cuts by camera markers.
blender -b build/sets.blend --python 03_anim.py [-- timing.json]
timing.json (Phase 2): {"S01": [cut_in, cut_out], ...}. Without it the clips run back to back at full length (Phase 1).
All keys are LINEAR (dense keys from functions), so nothing interpolates across a cut."""
import bpy, os, sys, json, math, random
from mathutils import Vector, Matrix
D_ = os.path.dirname(os.path.abspath(__file__))
exec(open(D_ + "/common.py").read())
exec(open(PIPE + "/anim_lib.py").read()); exec(open(PIPE + "/hand_poses.py").read()); exec(open(D_ + "/lib.py").read())
R = math.radians
sc = bpy.context.scene
sc.render.fps = 60; sc.render.resolution_x = 1080; sc.render.resolution_y = 1920
cams = bpy.data.collections.get("CAMS") or bpy.data.collections.new("CAMS")
if cams.name not in sc.collection.children: sc.collection.children.link(cams)
O = bpy.data.objects

# ------------------------------------------------------------------ shot table: (id, expected beat seconds, VO words in the reference)
SHOTS = [("S01", 1.5, "A man"), ("S02", 1.5, "fell behind a refrigerator unit"), ("S03", 2.0, "in the supermarket where he worked"),
         ("S04", 1.5, "in 2009"), ("S05", 1.0, "seriously trapped"), ("S06", 2.0, "but his cries for help"),
         ("S07", 1.5, "were drowned out by the noise"), ("S08", 1.5, "of the coolers"), ("S09", 1.5, "Days passed"),
         ("S10", 2.0, "and weeks turned into months"), ("S11", 1.5, "with no leads"), ("S12", 2.0, "on his whereabouts"),
         ("S13", 2.0, "ten years later"), ("S14", 1.5, "contractors began working"), ("S15", 1.5, "on the now abandoned supermarket"),
         ("S16", 2.0, "As they moved"), ("S17", 1.5, "the refrigerator unit"), ("S18", 1.0, "they found"),
         ("S19", 1.5, "the man's remains"), ("S20", 1.5, "wedged behind it")]
CLIP = {k: int(round(1.3 * s * 60)) for k, s, _ in SHOTS}
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if argv:
    T = {k: tuple(v) for k, v in json.load(open(argv[0])).items()}
else:
    T = {}; f = 1
    for k, s, _ in SHOTS: T[k] = (f, f + CLIP[k]); f += CLIP[k]
FEND = max(v[1] for v in T.values()) - 1
sc.frame_start = 1; sc.frame_end = FEND

# ------------------------------------------------------------------ set geometry (from 02_sets.py)
WALL_X = -10.75; BACK_X = -10.27; DEP = 0.85; HT = 2.15; FRONT_X = BACK_X + DEP
GAP_X = (WALL_X + BACK_X) / 2
hero = O["CoolerHero"]; n1 = O["CoolerN1"]; n2 = O["CoolerN2"]; fan = O["CondFan"]; skel = O["Skeleton"]
topboxes = [o for o in O if o.name.startswith("TopBox")]
debris = [o for o in O if o.name.startswith("Debris") or o.name.endswith("_Mark")]
shelves_full = [O["ShelfL"], O["ShelfR"]]; shelves_empty = [O["ShelfL_Empty"], O["ShelfR_Empty"]]
lamps = [o for o in O if o.name.startswith("StoreArea")]
LAMP_E = lamps[0].data.energy
hero_y = {"y": 0.0}
def ground(x, y):
    """cooler-bank tops are walkable in 2009 (x inside the bank depth, |y| < 3)"""
    if BACK_X <= x <= FRONT_X and abs(y) < 3.0 and GZ.get("top", False): return HT + 0.03
    return 0.0
GZ["fn"] = ground

# ------------------------------------------------------------------ characters
class Actor(Man):
    def stand_g(self, f, xy, yaw=0.0, crouch=0.0, flex=0.0, side=0.0, gz=0.0, stance=1.0):
        p = Vector((xy[0], xy[1], self.hip.z - crouch + gz))
        self.h.key_root(f, p, yaw=yaw, flex=flex, side=side)
        for s in "LR":
            fx = self.h.foot_xy(s, p, yaw); c = Vector((xy[0], xy[1])); fx = c + (fx - c) * stance
            self.h.key_foot(s, f, fx, yaw)
    def arms_swing(self, f, ph, amp=0.10):
        """walking arms: bent, swinging opposite to the legs (ph in cycles)"""
        a = math.sin(2 * math.pi * ph)
        self.hang("L", f, fwd=amp * a, out=0.02, lift=0.03 + 0.03 * abs(a))
        self.hang("R", f, fwd=-amp * a, out=0.02, lift=0.03 + 0.03 * abs(a))
    def arm_to(self, s, f, W, d, n, pole=None, pose="relaxed"):
        self.hand(s, f, W, d, n, pole); apply_pose(self.o, s, pose, f)
    def root_world(self):
        pb = self.r.PB["root"]; return self.o.matrix_world @ pb.matrix @ self.r.rest("root").inverted()

wk = Actor("Worker"); mg = Actor("Manager"); dt = Actor("Detective"); ca = Actor("ConA"); cb = Actor("ConB")
ACT = [wk, mg, dt, ca, cb]
def show_rig(a, t, on):
    for ob in [a.o] + list(a.o.children_recursive):
        ob.hide_render = not on; ob.hide_viewport = not on
        ob.keyframe_insert("hide_render", frame=t); ob.keyframe_insert("hide_viewport", frame=t)
def show(objs, t, on):
    for o in objs:
        for ob in [o] + list(o.children_recursive):
            ob.hide_render = not on; ob.hide_viewport = not on
            ob.keyframe_insert("hide_render", frame=t); ob.keyframe_insert("hide_viewport", frame=t)
def base(a, t, xy, yaw=0.0, gz=0.0, pitch=0.0, turn=0.0):
    a.stand_g(t, xy, yaw, gz=gz); a.spine(t, pitch=pitch, turn=turn); a.jaw(t, 0); a.eyes(t)
    sc.frame_set(t)
    for s in "LR": a.hang(s, t)

def mark(k, c):
    mk = sc.timeline_markers.new(k, frame=T[k][0]); mk.camera = c
def catch(c, d=0.05, energy=1.2):
    nm = c.name + "_Catch"
    L = O.get(nm) or bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'POINT'))
    if L.name not in cams.objects: cams.objects.link(L)
    L.data.energy = energy; L.data.shadow_soft_size = 0.02; L.parent = c; L.location = (0, d, 0); L.data.use_shadow = False
    L.hide_render = True; L.keyframe_insert("hide_render", frame=1)
    for k in T:
        if k == c.name[4:]:
            L.hide_render = False; L.keyframe_insert("hide_render", frame=T[k][0])
            L.hide_render = True; L.keyframe_insert("hide_render", frame=T[k][1])
def cam_path(c, t, L, keys):
    """keys: [(u, eye, target)] with u in 0..1, smooth between"""
    for i in range(0, L + 1, 3):
        u = i / L
        for j in range(len(keys) - 1):
            if keys[j][0] <= u <= keys[j + 1][0]:
                v = smooth((u - keys[j][0]) / (keys[j + 1][0] - keys[j][0]))
                e = Vector(keys[j][1]).lerp(Vector(keys[j + 1][1]), v); g = Vector(keys[j][2]).lerp(Vector(keys[j + 1][2]), v)
                look(c, t + i, e, g)
                break

# ------------------------------------------------------------------ era state per shot
GAPLIGHT = O.get("GapLight") or bpy.data.objects.new("GapLight", bpy.data.lights.new("GapLight", 'AREA'))
if GAPLIGHT.name not in cams.objects: cams.objects.link(GAPLIGHT)
GAPLIGHT.data.shape = 'RECTANGLE'; GAPLIGHT.data.size = 0.4; GAPLIGHT.data.size_y = 1.6
GAPLIGHT.location = (GAP_X + 0.05, 0.0, 3.3); GAPLIGHT.rotation_euler = (0, 0, 0); GAPLIGHT.data.color = (1.0, 0.95, 0.88)
def era(t, year, gap_light=0.0):
    GZ["top"] = (year == 2009)
    show(shelves_full, t, year == 2009); show(shelves_empty, t, year == 2019)
    show([n1, n2] + topboxes, t, year == 2009); show(debris, t, year == 2019)
    show([skel], t, year == 2019)
    for l in lamps:
        l.data.energy = LAMP_E if year == 2009 else LAMP_E * 0.55
        l.data.color = (1.0, 0.96, 0.9) if year == 2009 else (0.82, 0.88, 1.0)
        l.data.keyframe_insert("energy", frame=t); l.data.keyframe_insert("color", frame=t)
    GAPLIGHT.data.energy = gap_light; GAPLIGHT.data.keyframe_insert("energy", frame=t)
def cast(t, who):
    for a in ACT: show_rig(a, t, a in who)

# fan spins all film long (the coolers' noise)
fan.rotation_mode = 'XYZ'
fan.rotation_euler = (0, 0, 0); fan.keyframe_insert("rotation_euler", index=0, frame=1)
fan.rotation_euler = (FEND * 0.45, 0, 0); fan.keyframe_insert("rotation_euler", index=0, frame=FEND)

# hero cooler position (2009 in place; 2019 slid +Y by the contractors in S16/S17)
def hero_at(f, y):
    hero.location = (BACK_X, y, 0); hero.keyframe_insert("location", frame=f)
SKEL_XY = (GAP_X, -0.55)
skel.location = (SKEL_XY[0], SKEL_XY[1], 0.0); skel.rotation_mode = 'XYZ'
skel.rotation_euler = (0, R(-5), R(90)); skel.keyframe_insert("location", frame=1); skel.keyframe_insert("rotation_euler", frame=1)

# ===================================================================== 2009
GAP_Y = -0.45                                   # where he drops into the gap (behind the hero unit, clear of the condensing unit)
TOP_X = BACK_X + 0.40                           # walking line on the cooler tops
def S01(t, L):
    """he walks along the cooler tops (careful steps, arms swinging), toward the hero unit"""
    era(t, 2009); cast(t, [wk]); hero_at(t, 0.0)
    y0, y1 = -2.3, GAP_Y - 0.05
    path = lambda f: Vector((TOP_X, y0 + (y1 - y0) * smooth(min(1, (f - t) / (L * 0.85))), 0))
    yaw = lambda f: 180.0
    wk.h.walk(path, yaw, t, t + L, stride=0.55, lift=0.07, lean=4, step=2)
    for i in range(0, L + 1, 3):
        f = t + i; sc.frame_set(f)
        wk.arms_swing(f, (path(f).y - y0) / 0.55 * 0.5, amp=0.08)
        wk.spine(f, flex=4, pitch=-7 + 3 * math.sin(i / 20), turn=6)       # looking down at his footing, face to camera
        wk.eyes(f, pitch=-6)
    c = cam("CAM_S01", 32, 8); catch(c)
    cam_path(c, t, L, [(0, (-8.1, 0.9, 3.25), (TOP_X, -1.9, 3.0)), (1, (-8.3, 0.8, 3.2), (TOP_X, -0.8, 3.0))])
    mark("S01", c)

def S02(t, L):
    """steps back toward the wall to turn round, heel slips off the back edge, drops feet-first into the gap, arms up"""
    era(t, 2009); cast(t, [wk]); hero_at(t, 0.0)
    x0 = TOP_X; yy = GAP_Y; tf = int(L * 0.38); td = int(L * 0.62)
    for i in range(0, L + 1, 2):
        f = t + i; u = i / L
        if i <= tf:                                  # small backward steps toward the edge, facing the store (+X)
            k = smooth(i / tf); x = x0 - 0.30 * k
            wk.stand_g(f, (x, yy), yaw=90, gz=HT, stance=0.9)
            wk.spine(f, flex=4, pitch=-8, turn=0)
            sc.frame_set(f); wk.hang("L", f, out=0.05 + 0.1 * k); wk.hang("R", f, out=0.05 + 0.1 * k)
        elif i <= td:                                # heel off the edge: tips back, arms fly up
            k = (i - tf) / (td - tf); kk = k * k
            x = x0 - 0.30 - 0.06 * k
            gz = HT - 0.25 * kk
            p = Vector((x - 0.05 * k, yy, wk.hip.z + gz))
            wk.h.key_root(f, p, yaw=90, flex=-14 * k)
            for s in "LR":
                fx = wk.h.foot_xy(s, p, 90); lift = gz - ground(fx.x, fx.y) + 0.06 * k
                wk.h.key_foot(s, f, fx + Vector((0.10 * k, 0)), 90, lift=max(0.0, lift), pitch=-10 * k)
            wk.spine(f, flex=-8 * k, pitch=-25 * k); wk.jaw(f, 7 * k)
            sc.frame_set(f); rw = wk.root_world()
            for s, sx in (("L", 1), ("R", -1)):
                sh = rw @ wk.r.BN["upperarm01." + s].head_local
                Wp = sh + Vector((0.10, -sx * 0.25 * 0 + sx * 0.0, 0)) + Vector((0.05, 0, 0)) + (Vector((0, 0, -0.45)).lerp(Vector((0, 0, 0.42)), smooth(k)))
                Wp = Vector((Wp.x, sh.y + (0.30 if s == "R" else -0.30) * smooth(k) * 0 + (sh.y - rw.translation.y) * 0.6, Wp.z))
                wk.arm_to(s, f, Wp, Vector((0, 0, 1)).lerp(Vector((0, 0, -1)), 1 - smooth(k)), Vector((1, 0, 0)), pose="open_alarm" if k > 0.5 else "relaxed")
        else:                                        # drop into the gap (accelerating), lands knees bent, arms still up
            k = (i - td) / (L - td); fall = min(1.0, (k / 0.55) ** 2)
            x = GAP_X - 0.09; gz = (HT - 0.25) * (1 - fall)
            crouch = 0.03 * smooth(max(0, (k - 0.55) / 0.45))
            p = Vector((x, yy, wk.hip.z + gz - crouch))
            wk.h.key_root(f, p, yaw=90, flex=-4 + 4 * fall)
            for s in "LR":
                fx = wk.h.foot_xy(s, p, 90)
                wk.h.key_foot(s, f, fx, 90, lift=max(0.0, gz + 0.03 * (1 - fall)))
            wk.spine(f, flex=-4, pitch=-30 + 5 * fall); wk.jaw(f, 7)
            sc.frame_set(f); rw = wk.root_world()
            for s in "LR":
                sh = rw @ wk.r.BN["upperarm01." + s].head_local
                wk.arm_to(s, f, Vector((sh.x + 0.06, sh.y + (sh.y - rw.translation.y) * 0.5, sh.z + 0.42)), Vector((0, 0, 1)), Vector((1, 0, 0)), pose="open_alarm")
    c = cam("CAM_S02", 28, 8); catch(c)
    cam_path(c, t, L, [(0, (-8.3, -2.2, 4.05), (BACK_X, GAP_Y + 0.2, 2.6)), (1, (GAP_X + 0.55, GAP_Y - 1.3, 4.25), (GAP_X, GAP_Y, 1.7))])
    mark("S02", c)

def wedged(a, f, i, L, mood=0.0, wave=0.0):
    """wedged upright in the 48 cm gap, chest to the cooler back, knees slightly bent, face up calling, arms reaching up (no contact)"""
    p = Vector((GAP_X - 0.09, GAP_Y, a.hip.z - 0.03 + 0.01 * math.sin(i / 9)))
    a.h.key_root(f, p, yaw=90, flex=0, side=4 * math.sin(i / 14 + mood))
    for s, fy in (("L", 135), ("R", 45)): a.h.key_foot(s, f, a.h.foot_xy(s, p, 90) + Vector((-0.03, 0)), fy)   # feet splayed along the gap, toes clear of the cooler back
    a.spine(f, flex=-6, pitch=-38 + 4 * math.sin(i / 11), turn=6 * math.sin(i / 17 + mood))
    a.jaw(f, 6 + 4 * max(0, math.sin(i / 7))); a.eyes(f, pitch=14)
    sc.frame_set(f); rw = a.root_world()
    for s, ph in (("L", 0.0), ("R", 1.7)):
        sh = rw @ a.r.BN["upperarm01." + s].head_local; side = (sh.y - rw.translation.y)
        up = 0.38 + 0.08 * math.sin(i / 8 + ph) * wave
        a.arm_to(s, f, Vector((GAP_X - 0.02, sh.y + side * 0.9, sh.z + up + 0.06)), Vector((0, side * 0.5, 1)), Vector((-1, 0, 0)), pose="open_alarm")

def S03(t, L):
    """crane from the aisle up over the cooler bank: the supermarket, and the narrow gap behind it with him inside"""
    era(t, 2009, gap_light=60); cast(t, [wk]); hero_at(t, 0.0)
    for i in range(0, L + 1, 3): wedged(wk, t + i, i, L, 0.3, 0.6)
    c = cam("CAM_S03", 24, 8); catch(c, energy=0.0)
    cam_path(c, t, L, [(0, (-5.6, 0.2, 1.7), (-10.0, -0.2, 1.4)), (1, (-9.75, -1.75, 4.3), (GAP_X, GAP_Y, 1.3))])
    mark("S03", c)
def S04(t, L):
    era(t, 2009, gap_light=60); cast(t, [wk]); hero_at(t, 0.0)
    for i in range(0, L + 1, 3): wedged(wk, t + i, i + 200, L, 1.0, 1.0)
    c = cam("CAM_S04", 26, 8); catch(c)
    cam_path(c, t, L, [(0, (GAP_X + 0.08, GAP_Y - 1.7, 4.2), (GAP_X, GAP_Y, 1.0)), (1, (GAP_X + 0.06, GAP_Y - 1.45, 4.1), (GAP_X, GAP_Y, 1.1))])
    mark("S04", c)
def S05(t, L):
    era(t, 2009, gap_light=60); cast(t, [wk]); hero_at(t, 0.0)
    for i in range(0, L + 1, 3): wedged(wk, t + i, i + 400, L, 2.0, 1.4)
    c = cam("CAM_S05", 40, 8); catch(c)
    cam_path(c, t, L, [(0, (GAP_X + 0.15, GAP_Y - 1.0, 3.75), (GAP_X, GAP_Y, 1.55)), (1, (GAP_X + 0.15, GAP_Y - 0.85, 3.55), (GAP_X, GAP_Y, 1.6))])
    mark("S05", c)
def S06(t, L):
    era(t, 2009, gap_light=60); cast(t, [wk]); hero_at(t, 0.0)
    for i in range(0, L + 1, 3): wedged(wk, t + i, i + 600, L, 3.0, 1.0)
    c = cam("CAM_S06", 55, 8); catch(c)
    sc.frame_set(t + L // 2); hd = wk.o.matrix_world @ wk.r.PB["head"].head
    cam_path(c, t, L, [(0, (GAP_X + 0.04, hd.y - 0.6, hd.z + 1.55), hd + Vector((0, 0, 0.08))), (1, (GAP_X + 0.04, hd.y - 0.5, hd.z + 1.3), hd + Vector((0, 0, 0.08)))])
    mark("S06", c)
def S07(t, L):
    """cooler fronts humming: push along the glass doors (he is behind them, unseen)"""
    era(t, 2009); cast(t, []); hero_at(t, 0.0)
    c = cam("CAM_S07", 30, 8)
    cam_path(c, t, L, [(0, (-7.3, -2.2, 1.45), (FRONT_X, -0.6, 1.3)), (1, (-7.7, -0.6, 1.5), (FRONT_X, 0.6, 1.3))])
    mark("S07", c)
def S08(t, L):
    """the condensing unit on top: fan spinning behind its grille"""
    era(t, 2009); cast(t, []); hero_at(t, 0.0)
    c = cam("CAM_S08", 45, 9)
    g = Vector((BACK_X + 0.54, 0.62, HT + 0.22))
    cam_path(c, t, L, [(0, (g.x + 1.3, g.y - 0.75, g.z + 0.35), g), (1, (g.x + 0.95, g.y - 0.45, g.z + 0.25), g)])
    mark("S08", c)

# --- the search: manager + detective in the cross-aisle in front of the coolers
MEET = Vector((-8.3, 0.0))
def talk_pose(a, f, i, yaw, xy, nod=0.0, shake=0.0, shrug=0.0, talk=0.0):
    a.stand_g(f, xy, yaw)
    a.spine(f, flex=3, pitch=nod * math.sin(i / 9), turn=shake * math.sin(i / 7))
    a.jaw(f, talk * max(0, math.sin(i / 5)) * 6)
    sc.frame_set(f)
    if shrug > 0:
        rw = a.root_world()
        for s in "LR":
            sh = rw @ a.r.BN["upperarm01." + s].head_local; fwd = rw.to_3x3() @ Vector((0, -1, 0)); side = (sh - rw.translation); side.z = 0
            W = sh + fwd * 0.30 + side.normalized() * 0.12 * shrug + Vector((0, 0, -0.42 + 0.06 * shrug))
            a.arm_to(s, f, W, fwd + side.normalized() * 0.3, Vector((0, 0, 1)) * 1.0 + fwd * 0.2, pose="relaxed",
                     pole=sh + side.normalized() * 0.4 + Vector((0, 0, -0.3)) - fwd * 0.2)
    else:
        for s in "LR": a.hang(s, f)
def S09(t, L):
    """days passed: the manager and a detective walk in and meet in front of the coolers"""
    era(t, 2009); cast(t, [mg, dt]); hero_at(t, 0.0)
    m0, m1 = Vector((MEET.x, -3.6, 0)), Vector((MEET.x, -0.55, 0))
    d0, d1 = Vector((MEET.x + 0.1, 3.4, 0)), Vector((MEET.x + 0.1, 0.55, 0))
    for a, p0, p1, yw in ((mg, m0, m1, 180.0), (dt, d0, d1, 0.0)):
        path = lambda f, p0=p0, p1=p1: p0.lerp(p1, min(1, (f - t) / (L * 0.8)))
        a.h.walk(path, lambda f, yw=yw: yw, t, t + L, stride=0.7, step=2)
        for i in range(0, L + 1, 3):
            f = t + i; sc.frame_set(f); dd = (path(f) - p0).length
            if i < L * 0.8: a.arms_swing(f, dd / 0.7 * 0.5)
            else:
                for s in "LR": a.hang(s, f)
            a.spine(f, pitch=-3, turn=-12 if a is mg else 12)
    c = cam("CAM_S09", 26, 8); catch(c)
    cam_path(c, t, L, [(0, (-5.9, -0.2, 1.6), (MEET.x, 0, 1.35)), (1, (-6.4, -0.1, 1.55), (MEET.x, 0, 1.4))])
    mark("S09", c)
def S10(t, L):
    era(t, 2009); cast(t, [mg, dt]); hero_at(t, 0.0)
    for i in range(0, L + 1, 3):
        f = t + i
        talk_pose(mg, f, i, 180, (MEET.x, -0.55), nod=4, talk=1.0)
        talk_pose(dt, f, i, 0, (MEET.x + 0.1, 0.55), shake=10)
    c = cam("CAM_S10", 35, 8); catch(c)
    cam_path(c, t, L, [(0, (-6.9, 1.6, 1.6), (MEET.x, 0.3, 1.5)), (1, (-6.8, 1.2, 1.6), (MEET.x, 0.4, 1.55))])
    mark("S10", c)
def S11(t, L):
    era(t, 2009); cast(t, [mg, dt]); hero_at(t, 0.0)
    for i in range(0, L + 1, 3):
        f = t + i; k = smooth(min(1, i / (L * 0.4)))
        talk_pose(mg, f, i, 180, (MEET.x, -0.55), nod=3)
        talk_pose(dt, f, i, 0, (MEET.x + 0.1, 0.55), shrug=k, nod=-3, talk=0.6)
    c = cam("CAM_S11", 35, 8); catch(c)
    cam_path(c, t, L, [(0, (-7.1, -1.9, 1.6), (MEET.x, 0.4, 1.45)), (1, (-7.2, -1.6, 1.6), (MEET.x, 0.4, 1.5))])
    mark("S11", c)
def S12(t, L):
    """on his whereabouts: the detective turns and looks round the store; camera drifts up to the cooler bank top"""
    era(t, 2009); cast(t, [mg, dt]); hero_at(t, 0.0)
    for i in range(0, L + 1, 3):
        f = t + i; k = smooth(min(1, i / (L * 0.5)))
        talk_pose(mg, f, i, 180, (MEET.x, -0.55), nod=2)
        dt.stand_g(f, (MEET.x + 0.1, 0.55), 0 + 60 * k); dt.spine(f, flex=2, pitch=6 * k, turn=25 * k); sc.frame_set(f)
        for s in "LR": dt.hang(s, f)
    c = cam("CAM_S12", 28, 8); catch(c)
    cam_path(c, t, L, [(0, (-7.2, 1.8, 1.6), (MEET.x, 0.4, 1.45)), (1, (-7.3, 1.6, 2.1), (BACK_X, 0.3, 1.45))])
    mark("S12", c)

# ===================================================================== 2019
def S13(t, L):
    """ten years later: the same store, abandoned: empty gondolas, dimmer cool light, debris, one cooler left"""
    era(t, 2019); cast(t, []); hero_at(t, 0.0)
    c = cam("CAM_S13", 24, 8)
    cam_path(c, t, L, [(0, (-2.0, 0.0, 1.8), (-10.0, 0.0, 1.2)), (1, (-3.6, 0.0, 1.7), (-10.0, 0.0, 1.2))])
    mark("S13", c)
def S14(t, L):
    """two contractors walk down the aisle toward the cooler"""
    era(t, 2019); cast(t, [ca, cb]); hero_at(t, 0.0)
    for a, x0, yy in ((ca, -2.2, -0.35), (cb, -1.4, 0.40)):
        p0, p1 = Vector((x0, yy, 0)), Vector((x0 - 2.6, yy, 0))
        path = lambda f, p0=p0, p1=p1: p0.lerp(p1, (f - t) / L)
        a.h.walk(path, lambda f: -90.0, t, t + L, stride=0.75, step=2)
        for i in range(0, L + 1, 3):
            f = t + i; sc.frame_set(f); a.arms_swing(f, (path(f) - p0).length / 0.75 * 0.5)
            a.spine(f, pitch=-2, turn=0)
    c = cam("CAM_S14", 32, 8); catch(c)
    cam_path(c, t, L, [(0, (-5.4, 0.15, 1.5), (-2.0, 0.0, 1.45)), (1, (-6.4, 0.15, 1.5), (-4.0, 0.0, 1.45))])
    mark("S14", c)
CA_PUSH = Vector((FRONT_X - 0.22, -1.0)); CB_PUSH = Vector((BACK_X + 0.30, -1.0))
def push_pose(a, f, i, hx, hy0, pushing=1.0, look_turn=0.0):
    """standing at the cooler's -Y side panel, both palms flat on it (12 mm off the enamel), leaning in"""
    xy = (hx, hy0 - 0.50 - 0.03 * pushing)
    a.stand_g(f, xy, 180, crouch=0.04 * pushing, flex=8 * pushing, stance=1.0)
    a.spine(f, flex=10 * pushing, pitch=-6, turn=look_turn); sc.frame_set(f)
    rw = a.root_world()
    for s, dz in (("L", 0.0), ("R", 0.06)):
        sh = rw @ a.r.BN["upperarm01." + s].head_local
        palm = Vector((sh.x, hy0, sh.z - 0.10 + dz))
        place_hand(a.o, s, f, palm, Vector((0, 1, 0)), Vector((0, 0, 1)), skin=0.085)
        pb = a.r.PB["Pole_elbow." + s]; n = "Pole_elbow." + s
        pole = sh + Vector(((sh.x - rw.translation.x) * 2.0, -0.2, -0.45))
        pb.location = a.r.rest(n).to_3x3().inverted() @ (pole - a.r.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)
        apply_pose(a.o, s, "flat_palm", f)
def S15(t, L):
    """they reach the cooler; ConA points at it, ConB nods"""
    era(t, 2019); cast(t, [ca, cb]); hero_at(t, 0.0)
    for i in range(0, L + 1, 3):
        f = t + i; k = smooth(min(1, i / (L * 0.35)))
        ca.stand_g(f, (-8.2, -0.6), -70 + 0 * k); ca.spine(f, flex=2, pitch=-2, turn=10); sc.frame_set(f)
        rw = ca.root_world(); sh = rw @ ca.r.BN["upperarm01.R"].head_local
        tgt = Vector((FRONT_X, -0.3, 1.5)); dirv = (tgt - sh).normalized()
        W = sh.lerp(sh + dirv * 0.55 + Vector((0, 0, -0.05)), k) + Vector((0, 0, -0.45 * (1 - k)))
        ca.arm_to("R", f, W, dirv.lerp(Vector((0, 0, -1)), 1 - k), Vector((0, 0, -1)), pose="point" if k > 0.6 else "relaxed",
                  pole=sh + Vector((0.1, 0.35, -0.4)))
        ca.hang("L", f)
        cb.stand_g(f, (-7.9, 0.45), -110); cb.spine(f, flex=2, pitch=4 * math.sin(i / 8), turn=-6); sc.frame_set(f)
        for s in "LR": cb.hang(s, f)
    c = cam("CAM_S15", 30, 8); catch(c)
    cam_path(c, t, L, [(0, (-7.0, -2.4, 1.65), (-8.6, -0.1, 1.45)), (1, (-7.0, -2.0, 1.65), (-8.8, -0.1, 1.45))])
    mark("S15", c)
PUSH = 1.25
def pushing(t, L, y0, y1):
    for i in range(0, L + 1, 2):
        f = t + i; u = i / L; y = y0 + (y1 - y0) * smooth(u)
        hero_at(f, y + 1.0)                 # unit's -Y side panel at y
        push_pose(ca, f, i, CA_PUSH.x, y - 0.0)
        push_pose(cb, f, i, CB_PUSH.x + 0.05, y - 0.0)
def S16(t, L):
    """as they moved the unit: both push its side panel, it slides along the wall (logo on ConA's back)"""
    era(t, 2019); cast(t, [ca, cb])
    pushing(t, L, -1.0, -1.0 + PUSH * 0.55)
    c = cam("CAM_S16", 30, 8); catch(c)
    cam_path(c, t, L, [(0, (-8.0, -3.0, 1.55), (-9.6, -1.1, 1.35)), (1, (-8.1, -2.4, 1.55), (-9.7, -0.6, 1.35))])
    mark("S16", c)
def S17(t, L):
    era(t, 2019); cast(t, [ca, cb])
    pushing(t, L, -1.0 + PUSH * 0.55, -1.0 + PUSH)
    c = cam("CAM_S17", 26, 8); catch(c)
    cam_path(c, t, L, [(0, (-6.6, -2.3, 1.75), (-9.9, -0.2, 1.2)), (1, (-6.8, -2.0, 1.75), (-10.0, 0.0, 1.2))])
    mark("S17", c)
def S18(t, L):
    """they found: both straighten, step back from the side panel and stare into the gap"""
    era(t, 2019); cast(t, [ca, cb]); hero_at(t, PUSH)
    y = -1.0 + PUSH
    for i in range(0, L + 1, 3):
        f = t + i; k = smooth(min(1, i / (L * 0.5)))
        for a, x, tw in ((ca, CA_PUSH.x + 0.05 * k, -50), (cb, CB_PUSH.x + 0.30 * k, -40)):
            a.stand_g(f, (x, y - 0.53 - 0.12 * k), 180 + 70 * k); a.spine(f, flex=-3 * k, pitch=-4, turn=tw * k * 0.4)
            a.jaw(f, 4 * k); sc.frame_set(f)
            for s in "LR": a.hang(s, f, lift=0.02)
    c = cam("CAM_S18", 30, 8); catch(c)
    cam_path(c, t, L, [(0, (-10.55, -2.1, 1.55), (-9.7, -0.4, 1.55)), (1, (-10.5, -1.9, 1.55), (-9.7, -0.4, 1.55))])
    mark("S18", c)
def S19(t, L):
    """the man's remains: a clean skeleton standing wedged between the wall and where the cooler stood"""
    era(t, 2019); cast(t, [ca, cb]); hero_at(t, PUSH)
    y = -1.0 + PUSH
    for i in range(0, L + 1, 4):
        f = t + i
        ca.stand_g(f, (CA_PUSH.x + 0.05, y - 0.65), 280); ca.spine(f, pitch=-4); sc.frame_set(f)
        for s in "LR": ca.hang(s, f)
        cb.stand_g(f, (CB_PUSH.x + 0.30, y - 0.65), 280); cb.spine(f, pitch=-4); sc.frame_set(f)
        for s in "LR": cb.hang(s, f)
    c = cam("CAM_S19", 35, 8)
    cam_path(c, t, L, [(0, (-9.1, -1.9, 1.45), (GAP_X, SKEL_XY[1], 1.1)), (1, (-9.4, -1.6, 1.4), (GAP_X, SKEL_XY[1], 1.15))])
    mark("S19", c)
def S20(t, L):
    era(t, 2019); cast(t, [ca, cb]); hero_at(t, PUSH)
    y = -1.0 + PUSH
    for i in range(0, L + 1, 4):
        f = t + i
        ca.stand_g(f, (CA_PUSH.x + 0.05, y - 0.65), 280); ca.spine(f, pitch=-4); sc.frame_set(f)
        for s in "LR": ca.hang(s, f)
        cb.stand_g(f, (CB_PUSH.x + 0.30, y - 0.65), 280); cb.spine(f, pitch=-4); sc.frame_set(f)
        for s in "LR": cb.hang(s, f)
    c = cam("CAM_S20", 26, 8)
    cam_path(c, t, L, [(0, (-8.4, -3.0, 2.0), (GAP_X, -0.3, 1.0)), (1, (-8.0, -3.4, 2.1), (GAP_X, -0.3, 1.0))])
    mark("S20", c)

only = os.environ.get("ONLY", "")
for k, s, _ in SHOTS:
    if only and k not in only.split(","): continue
    t0, t1 = T[k]; L = t1 - t0 - 1
    globals()[k](t0, L); print("ANIM", k, t0, t1 - 1)
# everything linear (dense keys) so no interpolation crosses a cut
def all_fc(o):
    ad = o.animation_data
    if not ad or not ad.action: return []
    act = ad.action
    if hasattr(act, "fcurves") and len(act.fcurves): return list(act.fcurves)
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for bag in strip.channelbags: out += list(bag.fcurves)
    return out
ids = list(O) + [o.data for o in O if o.type in ('LIGHT', 'CAMERA')]
for o in ids:
    for fc in all_fc(o):
        cst = fc.data_path.startswith(("hide_", "color", "energy"))
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT' if cst else 'LINEAR'
fan.animation_data.action and None
sc.camera = O["CAM_S01"]
sc["SHOTS"] = json.dumps({k: [T[k][0], T[k][1] - 1] for k in T})
bpy.ops.wm.save_as_mainfile(filepath=BUILD + "/anim.blend")
print("ANIM saved", FEND)
