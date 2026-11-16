"""TenDimes: 22 shots as 1x clips (~30% longer than the expected beat), one camera per shot, hard cuts by camera markers.
blender -b build/sets.blend --python 03_anim.py [-- timing.json]
timing.json (Phase 2): {"S01": [cut_in, cut_out], ...}. Without it the clips run back to back at full length (Phase 1)."""
import bpy, os, sys, json, math, random
from mathutils import Vector, Matrix
D = os.path.dirname(os.path.abspath(__file__))
exec(open(D + "/common.py").read())
exec(open(PIPE + "/anim_lib.py").read()); exec(open(PIPE + "/hand_poses.py").read()); exec(open(D + "/lib.py").read())
R = math.radians
sc = bpy.context.scene
sc.render.fps = 60; sc.render.resolution_x = 1080; sc.render.resolution_y = 1920
cams = bpy.data.collections.get("CAMS") or bpy.data.collections.new("CAMS")
if cams.name not in sc.collection.children: sc.collection.children.link(cams)
SX = {k: v for k, v in sc["SETX"].items()}

SHOTS = [("S01", 2.0), ("S02", 1.6), ("S03", 2.0), ("S04", 1.5), ("S05", 2.2), ("S06", 2.0), ("S07", 1.4), ("S08", 1.4),
         ("S09", 1.2), ("S10", 1.6), ("S11", 1.6), ("S12", 1.4), ("S13", 1.8), ("S14", 1.4), ("S15", 1.4), ("S16", 1.4),
         ("S17", 1.8), ("S18", 1.6), ("S19", 1.6), ("S20", 1.4), ("S21", 1.8), ("S22", 1.6)]
CLIP = {k: int(round(1.3 * s * 60)) for k, s in SHOTS}
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if argv:
    T = {k: tuple(v) for k, v in json.load(open(argv[0])).items()}
else:
    T = {}; f = 1
    for k, s in SHOTS: T[k] = (f, f + CLIP[k]); f += CLIP[k]
FEND = max(v[1] for v in T.values()) - 1
sc.frame_start = 1; sc.frame_end = FEND

O = bpy.data.objects
for n in ("Singer", "Son", "Kidnapper", "Daughter"):
    if "IK_hand.L" not in O[n].pose.bones:
        print("CTRL add", n); make_human_ctrl(O[n])
        for s in "LR":
            lo = O[n].pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = R(-40); lo.ik_max_x = R(145)
sing = Man("Singer"); son = Man("Son"); kid = Man("Kidnapper"); dau = Man("Daughter")
MEN = [sing, son, kid, dau]
pile10, pile2, pileD, dime = (O[n] for n in ("DimePile10", "DimePile2", "DimePileD", "Dime"))
door = O["Room_Door"]
# payphone handset (joined from the model's loose parts near the cradle) + our own cord
PARTS = [O[n] for n in sc["PAY_PARTS"]]
def cen(o):
    vv = [o.matrix_world @ v.co for v in o.data.vertices]; return sum(vv, Vector()) / len(vv), vv
hs_parts = []; cord_old = None
for o in PARTS:
    c, vv = cen(o)
    if max(v.z for v in vv) - min(v.z for v in vv) > 0.35: cord_old = o
    elif c.z > O["Street_PayRoot"].location.z + 0.45: hs_parts.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in hs_parts: o.select_set(True)
bpy.context.view_layer.objects.active = hs_parts[0]; bpy.ops.object.join()
hand_set = bpy.context.view_layer.objects.active; hand_set.name = "Handset"
Mw = hand_set.matrix_world.copy(); hand_set.parent = None; hand_set.matrix_world = Mw
bpy.context.view_layer.objects.active = hand_set
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
HS_REST = hand_set.matrix_world.copy()
vv = [v.co for v in hand_set.data.vertices]
HS_LEN = max(v.z for v in vv) - min(v.z for v in vv)
print("HANDSET", hand_set.location, "len", HS_LEN, "cord", cord_old.name if cord_old else None)
if cord_old: cord_old.hide_render = cord_old.hide_viewport = True
# cord: a 3-point bezier keyed per frame (phone body -> sag -> handset bottom)
cu = bpy.data.curves.new("HandsetCord", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.004; cu.bevel_resolution = 3
sp = cu.splines.new('BEZIER'); sp.bezier_points.add(2)
for bp in sp.bezier_points: bp.handle_left_type = bp.handle_right_type = 'AUTO'
cord = bpy.data.objects.new("HandsetCord", cu)
O["Street_Payphone"].users_collection[0].objects.link(cord)
cm = bpy.data.materials.new("M_Cord"); cm.use_nodes = True; cm.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1)
cm.node_tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = 0.4; cu.materials.append(cm)
PB_ = O["Street_PayRoot"]; PAY_ANCHOR = Vector((hand_set.location.x - 0.03, hand_set.location.y - 0.01, PB_.location.z + 0.40))
def key_cord(f):
    sc.frame_set(f)
    M = hand_set.matrix_world; a = M.to_3x3() @ Vector((0, 0, 1))
    end = M.translation - a * (HS_LEN * 0.48)
    mid = (PAY_ANCHOR + end) / 2 + Vector((0, -0.04, -0.22 - 0.15 * max(0, 0.6 - (PAY_ANCHOR - end).length)))
    for bp, p in zip(sp.bezier_points, (PAY_ANCHOR, mid, end)):
        bp.co = p; bp.keyframe_insert("co", frame=f)
        bp.handle_left = p; bp.handle_right = p
def cord_static(f):
    vis(cord, f, True)

def begin(objs, t):
    for o in objs:
        for fc in all_fcurves(o):
            v = fc.evaluate(t - 1)
            while True:
                ks = [k for k in fc.keyframe_points if k.co.x >= t - 1 - 1e-3]
                if not ks: break
                fc.keyframe_points.remove(ks[-1])
            fc.update(); kp = fc.keyframe_points.insert(t - 1, v); kp.interpolation = 'CONSTANT'
    for o in objs:
        for c in o.constraints:
            if c.type == 'CHILD_OF':
                c.influence = 0.0; c.keyframe_insert("influence", frame=t)
                for fc in all_fcurves(o):
                    if fc.data_path.startswith('constraints'):
                        for k in fc.keyframe_points: k.interpolation = 'CONSTANT'

PROPS = [pile10, pile2, pileD, dime, hand_set]
def park(t, keep=()):
    for o in PROPS:
        if o in keep: continue
        key_obj(o, t, loc=(0, -30, -5)); vis(o, t, False)
    for m in MEN:
        if m not in keep:
            m.stand(t, (0, -40), 0)       # off every set
def show(o, t): vis(o, t, True)
def ease(u): return smooth(max(0.0, min(1.0, u)))
def track(t0, n, step, fn):
    for i in list(range(0, n + 1, step)) + ([n] if n % step else []):
        fn(t0 + i, i / n)
def mark(k, c):
    mk = sc.timeline_markers.new(k, frame=T[k][0]); mk.camera = c
def catch(c, d=0.06, energy=1.5):
    nm = c.name + "_Catch"
    L = O.get(nm) or bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'POINT'))
    if L.name not in cams.objects: cams.objects.link(L)
    L.data.energy = energy; L.data.shadow_soft_size = 0.02; L.parent = c; L.location = (0, d, 0); L.data.use_shadow = False
    L.visible_diffuse = True; L.visible_glossy = True

ALL = [m.o for m in MEN] + PROPS + [door, cord]

def eyes_pt(m):
    """world point between the eyes (current frame)"""
    pb = m.r.PB["head"]; Mh = m.o.matrix_world @ pb.matrix @ m.r.rest("head").inverted()
    B = m.r.BN; return Mh @ ((B["eye.L"].head_local + B["eye.R"].head_local) / 2)
def bone_w(m, n, tail=False):
    pb = m.r.PB[n]; return m.o.matrix_world @ (pb.tail if tail else pb.head)
def head_rest_pt(m, p):
    pb = m.r.PB["head"]; return m.o.matrix_world @ pb.matrix @ m.r.rest("head").inverted() @ p

def base(m, t, xy, yaw=0.0):
    m.stand(t, xy, yaw); m.spine(t); m.jaw(t, 0); m.eyes(t)
    for s in "LR": m.hang(s, t)

def fwd(yaw): return Vector((math.sin(R(yaw)), -math.cos(R(yaw)), 0))
def right(yaw): f = fwd(yaw); return Vector((f.y, -f.x, 0))   # character's right side (world)

def palm_up(m, s, f, yaw, fwd_d=0.30, up=-0.18, out=0.10, tilt=0.0):
    """palm-up hand held in front of the chest (offering / looking at coins). Returns the wanted wrist position."""
    sx = 1 if s == "L" else -1
    sh = m.r.BN["upperarm01." + s].head_local
    root = m.r.PB["root"]; Mr = m.o.matrix_world @ root.matrix @ m.r.rest("root").inverted()
    W = Mr @ Vector((sh.x * 0.4 + sx * out, sh.y - fwd_d, sh.z + up))
    Rz = Mr.to_3x3()
    d = Rz @ Vector((-sx * 0.35, -1.0, 0.15 + tilt)); n = Rz @ Vector((sx * 0.15, 0.0, 1.0))
    pole = Mr @ Vector((sh.x + sx * 0.45, sh.y + 0.35, sh.z - 0.35))
    m.h.key_hand(s, f, W, d, n, pole=pole)
    return W, d.normalized(), n.normalized()

def palm_centre(m, s):
    W = m.wrist_world(s); wr = W.translation
    k3 = m.o.matrix_world @ m.r.PB["finger3-1." + s].head; k2 = m.o.matrix_world @ m.r.PB["finger2-1." + s].head
    k5 = m.o.matrix_world @ m.r.PB["finger5-1." + s].head
    c = wr * 0.45 + k3 * 0.55
    d = (k3 - wr).normalized(); a = (k2 - k5).normalized()
    n = d.cross(a) if s == "L" else a.cross(d)
    return c, n.normalized(), d

def seat_pile(m, s, pile, t, lift=0.017):
    """pile resting on the palm at t, then carried by the wrist (Child Of, no gap)"""
    sc.frame_set(t); c, n, d = palm_centre(m, s)
    if n.z < 0: n = -n
    z = n; x = d - z * d.dot(z); x.normalize(); y = z.cross(x)
    C = Matrix.Translation(c + n * lift) @ Matrix((x, y, z)).transposed().to_4x4()
    key_matrix(pile, t, C); show(pile, t)
    H = Held(pile, m, s); H.grab(t); return H

def sing_jaw(m, f, u, k=1.0):
    m.jaw(f, k * (5 + 5 * math.sin(u * 23.0)) * (0.6 + 0.4 * math.sin(u * 7)))

def ear_pt(m, s):
    """world point just outside the ear on side s (head-bone carried)"""
    body = next(k for k in m.o.children if k.name.endswith(".body"))
    if not hasattr(m, "_ear"):
        m._ear = {}
    if s not in m._ear:
        B = m.r.BN; ez = B["eye.L"].head_local.z; gi = body.vertex_groups["head"].index
        sx = 1 if s == "L" else -1
        pts = [v.co for v in body.data.vertices if abs(v.co.z - (ez - 0.02)) < 0.02 and v.co.x * sx > 0 and any(g.group == gi and g.weight > 0.5 for g in v.groups)]
        ex = max(pts, key=lambda p: p.x * sx)
        m._ear[s] = Vector((ex.x, ex.y, ex.z))
    return head_rest_pt(m, m._ear[s])

# ============================================================================================ lights per set
LC = bpy.data.collections.get("LIGHTS") or bpy.data.collections.new("LIGHTS")
if LC.name not in sc.collection.children: sc.collection.children.link(LC)
def area(name, loc, tgt, size, energy, col=(1, 1, 1)):
    L = bpy.data.objects.new(name, bpy.data.lights.new(name, 'AREA')); LC.objects.link(L)
    L.data.shape = 'RECTANGLE'; L.data.size = size; L.data.size_y = size * 0.7; L.data.energy = energy; L.data.color = col
    L.location = loc; L.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return L
X = SX["CLUB"]
area("Club_Key", (X - 2.0, -3.0, 3.6), (X, -0.2, 1.4), 2.5, 420, (1.0, 0.92, 0.8))
area("Club_Fill", (X + 2.6, -2.6, 2.2), (X, -0.2, 1.4), 2.5, 180, (0.9, 0.95, 1.0))
area("Club_Back", (X, 1.8, 4.2), (X, -0.2, 1.5), 1.5, 150, (1.0, 0.85, 0.7))
area("Club_CurtainWash", (X, -2.0, 0.3), (X, 2.6, 2.5), 6.0, 360, (1.0, 0.8, 0.75))
area("Club_Hall", (X, -6.5, 3.0), (X, -6.5, -0.7), 8.0, 540, (1.0, 0.85, 0.65))
X = SX["ROOM"]
area("Room_Key", (X - 1.0, -2.5, 2.7), (X + 1.0, 0.6, 1.2), 3.0, 360, (1.0, 0.96, 0.9))
area("Room_Fill", (X + 2.0, -2.2, 2.0), (X + 1.0, 0.6, 1.2), 2.5, 156, (0.9, 0.95, 1.0))
area("Room_Top", (X, 0.0, 2.9), (X, 0.0, 0.0), 4.0, 240)
area("Room_HallLight", (X + 4.2, 0.4, 2.8), (X + 4.2, 0.4, 0.0), 1.5, 150)
X = SX["STREET"]
area("Street_Key", (X - 2.5, -4.0, 3.5), (X + 0.3, 0.3, 1.4), 4.0, 720, (1.0, 0.95, 0.85))
area("Street_Fill", (X + 3.0, -3.5, 2.0), (X + 0.3, 0.3, 1.4), 3.0, 240, (0.85, 0.92, 1.0))
X = SX["SUBURB"]
area("Sub_Key", (X - 4.0, -7.0, 5.0), (X + 1.0, -1.0, 1.2), 6.0, 1800, (1.0, 0.95, 0.85))
area("Sub_Fill", (X + 5.0, -6.0, 3.0), (X + 1.0, -1.0, 1.2), 5.0, 720, (0.85, 0.92, 1.0))
X = SX["CEMET"]
area("Cem_Key", (X - 4.0, -5.0, 5.0), (X, 0.3, 1.0), 6.0, 1560, (1.0, 0.95, 0.85))
area("Cem_Fill", (X + 4.0, -4.0, 3.0), (X, 0.3, 1.0), 5.0, 600, (0.85, 0.92, 1.0))
area("Cem_Back", (X, 4.0, 4.0), (X, 0.5, 1.2), 4.0, 480)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); LC.objects.link(sun)
sun.data.energy = 1.4; sun.data.angle = R(8); sun.rotation_euler = (R(50), 0, R(-35))
w = sc.world or bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.7, 0.82, 0.95, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.6

# ============================================================================================ CLUB
CX = SX["CLUB"]; SING_CLUB = (CX, -0.12)
def S01(t, L):
    """'The singer': singing at the stand mic, right hand rises into an open-palm gesture"""
    begin(ALL, t); park(t, keep=(sing,)); base(sing, t, SING_CLUB)
    def fr(f, u):
        k = ease(u / 0.45)
        sing.spine(f, flex=-3, side=2 * math.sin(u * 5), pitch=-4 + 3 * math.sin(u * 4), turn=6 * math.sin(u * 3))
        sing.stand(f, SING_CLUB, yaw=4 * math.sin(u * 3))
        sing_jaw(sing, f, u)
        sh = sing.r.BN["upperarm01.R"].head_local
        W0 = Vector((sh.x - 0.12, sh.y - 0.10, sh.z - 0.47)); W1 = Vector((sh.x - 0.22, sh.y - 0.34, sh.z - 0.08 + 0.03 * math.sin(u * 6)))
        W = W0.lerp(W1, k) + Vector((CX, SING_CLUB[1], 0))
        d = Vector((-0.25, -0.4, -0.9)).lerp(Vector((-0.3, -0.45, 0.85)), k); n = Vector((-0.9, 0.2, 0)).lerp(Vector((0.1, -1.0, 0.2)), k)
        sing.hand("R", f, W, d, n, pole=Vector((CX + sh.x - 0.5, SING_CLUB[1] + 0.35, sh.z - 0.4)))
    track(t, L, 4, fr)
    apply_pose(sing.o, "R", "relaxed", t); apply_pose(sing.o, "R", "open_alarm", t + int(0.45 * L))
    c = cam("CAM_S01", 40, 8); catch(c, energy=2.0)
    look(c, t, (CX - 2.05, -2.45, 1.50), (CX - 0.05, -0.12, 1.32))
    look(c, t + L, (CX - 1.75, -2.10, 1.52), (CX - 0.03, -0.12, 1.38))
    mark("S01", c)

def S02(t, L):
    """'always had ten dimes': the ten dimes on his side table by the mic, the singer behind (no hand contact), push-in"""
    begin(ALL, t); park(t, keep=(sing, pile10)); base(sing, t, SING_CLUB, 15)
    TT = Vector(sc["TABLE_TOP"]); key_matrix(pile10, t, Matrix.Translation(TT)); show(pile10, t)
    def fr(f, u):
        sing.spine(f, flex=6, pitch=16 + 4 * ease(u), turn=8); sing.eyes(f, pitch=14, yaw=6); sing.stand(f, SING_CLUB, 15)
    track(t, L, 4, fr)
    c = cam("CAM_S02", 50, 11); catch(c)
    look(c, t, TT + Vector((0.10, -0.62, 0.30)), TT + Vector((-0.08, 0.10, 0.10)))
    look(c, t + L, TT + Vector((0.06, -0.42, 0.20)), TT + Vector((-0.05, 0.06, 0.06)))
    mark("S02", c)

def S03(t, L):
    """'And the reason for this is kind of sad': CU singing, eyes lower, head tilts"""
    begin(ALL, t); park(t, keep=(sing,)); base(sing, t, SING_CLUB)
    def fr(f, u):
        sing.spine(f, flex=-2, side=-3 * math.sin(u * 2.5), pitch=-6 + 10 * ease(u), turn=-8 + 6 * math.sin(u * 2))
        sing_jaw(sing, f, u, 0.8); sing.eyes(f, pitch=4 + 8 * ease(u))
    track(t, L, 4, fr)
    c = cam("CAM_S03", 60, 8); catch(c)
    sc.frame_set(t + L // 2); e = eyes_pt(sing)
    look(c, t, e + Vector((-0.72, -1.10, 0.02)), e + Vector((0, 0, -0.10)))
    look(c, t + L, e + Vector((-0.60, -0.95, 0.03)), e + Vector((0, 0, -0.08)))
    mark("S03", c)

# ============================================================================================ ROOM
RX = SX["ROOM"]; SON_ROOM = (RX + 0.5, 0.95)
def door_open(t, ang):
    door.rotation_euler = (0, 0, R(-ang)); door.keyframe_insert("rotation_euler", frame=t)
def S04(t, L):
    """'You see his son': son by the window turns, startled, toward the door (a knock)"""
    begin(ALL, t); park(t, keep=(son,)); base(son, t, SON_ROOM, 10); door_open(t, 0)
    def fr(f, u):
        k = ease((u - 0.3) / 0.35)
        son.stand(f, SON_ROOM, 10 + 55 * k)
        son.spine(f, flex=-2 * k, turn=25 * k, pitch=-4 * k, side=0)
        son.eyes(f, yaw=12 * k); son.jaw(f, 4 * k)
        for s in "LR": son.hang(s, f, out=0.04 * k, fwd=0.12 * k, lift=0.10 * k)
    track(t, L, 4, fr)
    c = cam("CAM_S04", 45, 8); catch(c)
    sc.frame_set(t); e = eyes_pt(son)
    look(c, t, e + Vector((0.55, -1.75, -0.05)), e + Vector((0.05, 0, -0.22)))
    look(c, t + L, e + Vector((0.70, -1.55, -0.03)), e + Vector((0.10, 0, -0.18)))
    mark("S04", c)

def S05(t, L):
    """'was kidnapped': a man in a dark jacket stands in the open doorway and points out; the son walks to the door"""
    begin(ALL, t); park(t, keep=(son, kid)); door_open(t, 80)
    KP = (RX + 2.05, 0.35)
    base(kid, t, KP, -90 + 20); base(son, t, SON_ROOM, 60)
    A = Vector((SON_ROOM[0], SON_ROOM[1], 0)); B_ = Vector((RX + 0.95, 0.20, 0))
    f0 = t + int(0.25 * L); f1 = t + L
    son.h.walk(lambda f: A.lerp(B_, ease((f - f0) / (f1 - f0))), lambda f: 105.0, f0, f1, stride=0.6, step=2, crouch=0.0, bob=0.012, lean=4.0)
    for f in range(t, f0 + 1, 4): son.stand(f, SON_ROOM, 60 + 45 * ease((f - t) / (f0 - t)))
    def fr(f, u):
        k = ease(u / 0.3)
        kid.stand(f, KP, -70 - 10 * k); kid.spine(f, turn=-10 * k, pitch=-3); kid.eyes(f)
        sh = kid.r.BN["upperarm01.L"].head_local
        Mr = kid.o.matrix_world @ kid.r.PB["root"].matrix @ kid.r.rest("root").inverted()
        if k > 0.01:
            W = Mr @ Vector((sh.x + 0.25, sh.y - 0.30, sh.z - 0.12)).lerp(Mr @ Vector((sh.x + 0.10, sh.y - 0.12, sh.z - 0.48)), 1 - k)
            kid.hand("L", f, W, Mr.to_3x3() @ Vector((0.75, -0.6, 0.05)), Mr.to_3x3() @ Vector((0, 0, -1)), pole=Mr @ Vector((sh.x + 0.3, sh.y + 0.5, sh.z - 0.3)))
        kid.hang("R", f)
        if f <= f0:
            son.spine(f, turn=10, pitch=-2); son.eyes(f, yaw=8)
            for s in "LR": son.hang(s, f)
        else:
            son.eyes(f, yaw=-6)
            for s in "LR":
                ph = (f - f0) / 60 * 2 * math.pi * 0.85 + (0 if s == "L" else math.pi)
                son.hang(s, f, fwd=0.10 * math.sin(ph), out=0.02)
    track(t, L, 2, fr)
    apply_pose(kid.o, "L", "relaxed", t); apply_pose(kid.o, "L", "point", t + int(0.3 * L))
    c = cam("CAM_S05", 30, 8); catch(c)
    look(c, t, (RX - 1.3, -2.6, 1.55), (RX + 1.25, 0.45, 1.15))
    look(c, t + L, (RX - 1.0, -2.3, 1.55), (RX + 1.45, 0.40, 1.15))
    mark("S05", c)

# ============================================================================================ STREET
PX = SX["STREET"]; SING_PH = (PX + 0.48, 0.12); PH_YAW = -20.0
def S06(t, L):
    """'years prior ... all of the calls': wide street; the singer walks along the brick wall to the payphone"""
    begin(ALL, t); park(t, keep=(sing, hand_set)); door_open(t, 0); show(hand_set, t); key_matrix(hand_set, t, HS_REST)
    A = Vector((PX + 2.0, -0.45, 0)); B_ = Vector((SING_PH[0] + 0.15, SING_PH[1] - 0.18, 0))
    f1 = t + int(0.82 * L)
    base(sing, t, (A.x, A.y), -90)
    sing.h.walk(lambda f: A.lerp(B_, (f - t) / (f1 - t)), lambda f: -90 + 50 * ease((f - t) / (f1 - t) * 1.4 - 0.4), t, f1, stride=0.72, step=2)
    def fr(f, u):
        if f <= f1:
            for s in "LR":
                ph = (f - t) / 60 * 2 * math.pi * 0.95 + (0 if s == "L" else math.pi)
                sing.hang(s, f, fwd=0.12 * math.sin(ph), out=0.02)
            sing.eyes(f, yaw=-10)
        else:
            k = ease((f - f1) / (t + L - f1)); sing.stand(f, (B_.x, B_.y), -40 + 20 * k)
            sing.spine(f, turn=-12 * k); sing.eyes(f, yaw=-12)
            for s in "LR": sing.hang(s, f)
    track(t, L, 2, fr)
    c = cam("CAM_S06", 30, 8); catch(c, energy=1.0)
    look(c, t, (PX + 0.2, -3.6, 1.5), (PX + 1.3, 0.2, 1.15))
    look(c, t + L, (PX - 0.1, -3.1, 1.5), (PX + 0.6, 0.2, 1.15))
    mark("S06", c)

def S07(t, L):
    """'had to be made from payphones': the street payphone (handset on its hook, cord), slow push-in; no hands"""
    begin(ALL, t); park(t, keep=(hand_set,)); show(hand_set, t); key_matrix(hand_set, t, HS_REST); vis(cord, t, False)
    if cord_old: vis(cord_old, t, True)
    c = cam("CAM_S07", 40, 11)
    ph = O["Street_PayRoot"].location + Vector((0.02, 0.0, 0.60))
    look(c, t, ph + Vector((-0.55, -1.25, 0.10)), ph + Vector((0.0, 0.0, -0.05)))
    look(c, t + L, ph + Vector((-0.40, -0.90, 0.06)), ph + Vector((0.0, 0.0, -0.03)))
    mark("S07", c)

def phone_hand(m, f, s="R", it=4):
    """handset locked to the head (earpiece 2.2 cm off the ear, mouthpiece toward the mouth); the hand is then driven so the
    palm wraps the handset's outer side (palm centre + 2.4 cm along the palm normal = handset centre)."""
    sc.frame_set(f)
    ear = ear_pt(m, s); e = eyes_pt(m)
    fw = (e - bone_w(m, "head")); fw.z = 0; fw.normalize()
    side = (ear - e); side.z = 0; side.normalize()
    top = ear + side * 0.048 + Vector((0, 0, 0.01))
    mouth = e + fw * 0.075 + Vector((0, 0, -0.105))
    bot = mouth + side * 0.055
    a = (top - bot).normalized()
    ctr = top - a * HS_LEN * 0.45
    y = -side; y = (y - a * y.dot(a)).normalized(); x = y.cross(a)
    C = Matrix.Translation(ctr) @ Matrix((x, y, a)).transposed().to_4x4()
    sh = bone_w(m, "upperarm01." + s)
    pole = sh + Vector((0, 0, -0.45)) + side * 0.35 + fw * 0.15
    W = ctr + side * 0.05 - a * 0.06
    for k in range(it):
        m.hand(s, f, W, a * 0.3 - fw * 0.7, -side, pole=pole)
        sc.frame_set(f)
        c, n, d = palm_centre(m, s)
        err = (ctr + side * 0.048) - c
        if err.length < 0.004: break
        W = W + err
    return C

def hold_phone(t, L, extra=None, cam_fn=None):
    begin(ALL, t); park(t, keep=(sing, hand_set)); show(hand_set, t); show(cord, t)
    if cord_old: vis(cord_old, t, False)
    base(sing, t, SING_PH, PH_YAW)
    apply_pose(sing.o, "R", "wrap_grip", t, amount=0.75)
    def fr(f, u):
        if extra: extra(f, u)
        key_matrix(hand_set, f, phone_hand(sing, f))
        key_cord(f)
    track(t, L, 3, fr)

def S08(t, L):
    """'He would': MCU, handset at his ear, waiting, eyes darting"""
    def ex(f, u):
        sing.stand(f, SING_PH, PH_YAW + 4 * math.sin(u * 3)); sing.spine(f, flex=3, pitch=4, turn=-6 * math.sin(u * 2.5))
        sing.eyes(f, yaw=10 * math.sin(u * 5)); sing.hang("L", f)
    hold_phone(t, L, ex)
    c = cam("CAM_S08", 45, 8); catch(c)
    sc.frame_set(t); e = eyes_pt(sing)
    look(c, t, e + fwd(PH_YAW) * 1.25 + right(PH_YAW) * -0.55 + Vector((0, 0, -0.08)), e + Vector((0, 0, -0.22)))
    look(c, t + L, e + fwd(PH_YAW) * 1.05 + right(PH_YAW) * -0.45 + Vector((0, 0, -0.06)), e + Vector((0, 0, -0.18)))
    mark("S08", c)

def S09(t, L):
    """'terrified': CU, brows up, mouth slightly open, a small pull-back of the head"""
    def ex(f, u):
        k = ease(u / 0.4)
        sing.stand(f, SING_PH, PH_YAW); sing.spine(f, flex=-4 * k, pitch=-6 * k, turn=-4)
        sing.eyes(f, pitch=-4 * k, yaw=-4); sing.jaw(f, 1.5 * k); sing.hang("L", f)
    hold_phone(t, L, ex)
    c = cam("CAM_S09", 70, 8); catch(c, energy=2.0)
    sc.frame_set(t); e = eyes_pt(sing)
    look(c, t, e + fwd(PH_YAW) * 0.85 + right(PH_YAW) * -0.22 + Vector((0, 0, 0.0)), e + Vector((0, 0, -0.04)))
    look(c, t + L, e + fwd(PH_YAW) * 0.70 + right(PH_YAW) * -0.18 + Vector((0, 0, 0.0)), e + Vector((0, 0, -0.03)))
    mark("S09", c)

def S10(t, L):
    """'that he would run out of coins': the last two dimes on the ledge under the phone; he glances down, handset at his ear"""
    LT = Vector(sc["LEDGE_TOP"]); key_matrix(pile2, t, Matrix.Translation(LT))
    def ex(f, u):
        sing.stand(f, SING_PH, PH_YAW); sing.spine(f, flex=6, pitch=14 * ease(u / 0.4), turn=10); sing.eyes(f, pitch=14 * ease(u / 0.4), yaw=8)
        sing.hang("L", f)
    hold_phone(t, L, ex)
    park(t, keep=(sing, hand_set, pile2)); show(pile2, t); key_matrix(pile2, t, Matrix.Translation(LT))
    c = cam("CAM_S10", 50, 11); catch(c)
    look(c, t, LT + Vector((-0.42, -0.80, 0.22)), LT + Vector((0.12, 0.0, 0.12)))
    look(c, t + L, LT + Vector((-0.36, -0.68, 0.20)), LT + Vector((0.12, 0.0, 0.11)))
    mark("S10", c)

def S11(t, L):
    """'to negotiate with the kidnappers': MS, talking urgently into the handset, free hand open, pleading"""
    def ex(f, u):
        sing.stand(f, SING_PH, PH_YAW - 6 * math.sin(u * 2)); sing.spine(f, flex=6, pitch=6, turn=6 * math.sin(u * 3))
        sing_jaw(sing, f, u, 0.9); sing.eyes(f, yaw=-6)
        sh = sing.r.BN["upperarm01.L"].head_local
        Mr = sing.o.matrix_world @ sing.r.PB["root"].matrix @ sing.r.rest("root").inverted()
        k = 0.5 + 0.5 * math.sin(u * 6)
        sing.hand("L", f, Mr @ Vector((sh.x - 0.02, sh.y - 0.32, sh.z - 0.30 + 0.05 * k)), Mr.to_3x3() @ Vector((-0.3, -0.8, 0.5)), Mr.to_3x3() @ Vector((-0.5, 0, 1)),
                  pole=Mr @ Vector((sh.x + 0.45, sh.y + 0.3, sh.z - 0.35)))
    hold_phone(t, L, ex)
    apply_pose(sing.o, "L", "open_alarm", t)
    c = cam("CAM_S11", 35, 8); catch(c)
    sc.frame_set(t); e = eyes_pt(sing)
    look(c, t, e + fwd(PH_YAW) * 1.9 + right(PH_YAW) * -0.85 + Vector((0, 0, -0.25)), e + Vector((0, 0, -0.35)))
    look(c, t + L, e + fwd(PH_YAW) * 1.6 + right(PH_YAW) * -0.55 + Vector((0, 0, -0.22)), e + Vector((0, 0, -0.32)))
    mark("S11", c)

# ============================================================================================ SUBURB
UX = SX["SUBURB"]; FATHER = (UX + 0.6, -1.0)
def S12(t, L):
    """'two days later': wide, the singer walks along the suburban pavement, the black car waits at the kerb"""
    begin(ALL, t); park(t, keep=(sing,))
    A = Vector((UX - 2.4, -1.0, 0)); B_ = Vector((FATHER[0], FATHER[1], 0))
    base(sing, t, (A.x, A.y), 90)
    sing.h.walk(lambda f: A.lerp(B_, (f - t) / L), lambda f: 90.0, t, t + L, stride=0.72, step=2)
    def fr(f, u):
        for s in "LR":
            ph = (f - t) / 60 * 2 * math.pi * 0.95 + (0 if s == "L" else math.pi)
            sing.hang(s, f, fwd=0.12 * math.sin(ph), out=0.02)
        sing.eyes(f, yaw=10)
    track(t, L, 2, fr)
    c = cam("CAM_S12", 28, 8); catch(c, energy=1.0)
    look(c, t, (UX + 1.2, -3.9, 1.45), (UX - 1.2, -0.8, 1.1))
    look(c, t + L, (UX + 1.6, -3.5, 1.45), (UX + 0.2, -0.8, 1.1))
    mark("S12", c)

def S13(t, L):
    """'the son was released': the son walks from the car toward his father"""
    begin(ALL, t); park(t, keep=(sing, son)); base(sing, t, FATHER, 90)
    A = Vector((UX + 2.3, -1.45, 0)); B_ = Vector((FATHER[0] + 0.62, FATHER[1] - 0.05, 0))
    base(son, t, (A.x, A.y), -110)
    son.h.walk(lambda f: A.lerp(B_, (f - t) / L), lambda f: -100.0, t, t + L, stride=0.66, step=2, crouch=0.0, bob=0.012, lean=4.0)
    def fr(f, u):
        for s in "LR":
            ph = (f - t) / 60 * 2 * math.pi * 0.9 + (0 if s == "L" else math.pi)
            son.hang(s, f, fwd=0.10 * math.sin(ph), out=0.02)
        son.eyes(f, yaw=-4)
        k = ease(u / 0.6)
        sing.stand(f, FATHER, 90 + 5 * k); sing.spine(f, flex=-2 * k, pitch=-3 * k); sing.jaw(f, 3 * k)
        for s in "LR": sing.hang(s, f, fwd=0.12 * k, lift=0.08 * k, out=0.03 * k)
    track(t, L, 2, fr)
    c = cam("CAM_S13", 32, 8); catch(c)
    look(c, t, (UX + 0.4, -4.8, 1.5), (UX + 1.6, -1.4, 1.25))
    look(c, t + L, (UX + 0.6, -4.3, 1.5), (UX + 1.2, -1.2, 1.25))
    mark("S13", c)

def S14(t, L):
    """'safely': father and son face each other; the father's hands rest on the son's shoulders"""
    begin(ALL, t); park(t, keep=(sing, son))
    SP = (FATHER[0] + 0.56, FATHER[1] - 0.04)
    base(sing, t, FATHER, 90); base(son, t, SP, -90)
    def fr(f, u):
        k = ease(u / 0.45)
        sing.stand(f, FATHER, 90); sing.spine(f, flex=4 * k, pitch=4); sing.jaw(f, 2 * k)
        son.stand(f, SP, -90); son.spine(f, flex=2, pitch=-3 + 2 * math.sin(u * 3)); son.eyes(f, pitch=-3)
        for s in "LR": son.hang(s, f)
        sc.frame_set(f)
        for s, os_ in (("L", "R"), ("R", "L")):
            sh = bone_w(son, "upperarm01." + os_) + Vector((0, 0, 0.055))       # top of the son's shoulder
            sx = 1 if s == "L" else -1
            hs = bone_w(sing, "upperarm01." + s)
            rest = hs + Vector((0.18, 0, -0.45))
            P = rest.lerp(sh + Vector((-0.02, 0, 0.0)), k)
            place_hand(sing.o, s, f, P, Vector((0.25, 0, -1)).lerp(Vector((0, 0, -1)), k), Vector((1, 0, -0.2)), skin=0.012)
    track(t, L, 3, fr)
    for s in "LR": apply_pose(sing.o, s, "relaxed", t); apply_pose(sing.o, s, "cup_hold", t + int(0.45 * L))
    c = cam("CAM_S14", 38, 8); catch(c)
    look(c, t, (FATHER[0] + 0.25, -3.05, 1.55), (FATHER[0] + 0.28, -1.0, 1.42))
    look(c, t + L, (FATHER[0] + 0.30, -2.75, 1.56), (FATHER[0] + 0.28, -1.0, 1.44))
    mark("S14", c)

def S15(t, L):
    """'But he never forgot that fear': CU, the father looks down, then away, jaw tight"""
    begin(ALL, t); park(t, keep=(sing,)); base(sing, t, FATHER, 20)
    def fr(f, u):
        sing.spine(f, flex=4, pitch=10 * ease(u / 0.5), turn=-10 + 14 * ease(u)); sing.eyes(f, pitch=10 * ease(u / 0.5), yaw=6)
    track(t, L, 4, fr)
    c = cam("CAM_S15", 60, 8); catch(c)
    sc.frame_set(t); e = eyes_pt(sing)
    look(c, t, e + fwd(20) * 1.05 + right(20) * 0.30 + Vector((0, 0, -0.05)), e + Vector((0, 0, -0.10)))
    look(c, t + L, e + fwd(20) * 0.90 + right(20) * 0.24 + Vector((0, 0, -0.04)), e + Vector((0, 0, -0.08)))
    mark("S15", c)

def S16(t, L):
    """'of being helpless': ECU push-in, eyes glisten, a slow breath"""
    begin(ALL, t); park(t, keep=(sing,)); base(sing, t, FATHER, 20)
    def fr(f, u):
        sing.spine(f, flex=2 + 2 * math.sin(u * 3), pitch=-2 - 2 * math.sin(u * 2), turn=4); sing.eyes(f, pitch=-2, yaw=-2)
        sing.jaw(f, 0.0)
    track(t, L, 4, fr)
    c = cam("CAM_S16", 85, 8); catch(c, energy=2.0)
    sc.frame_set(t); e = eyes_pt(sing)
    look(c, t, e + fwd(20) * 1.0 + Vector((0, 0, 0.0)), e + Vector((0, 0, -0.04)))
    look(c, t + L, e + fwd(20) * 0.78 + Vector((0, 0, 0.0)), e + Vector((0, 0, -0.03)))
    mark("S16", c)

# ============================================================================================ CLUB again (later years)
def S17(t, L):
    """'So he carried ten dimes exactly with him': years later at the club, he looks down at the ten dimes on his side table and smiles"""
    begin(ALL, t); park(t, keep=(sing, pile10)); base(sing, t, SING_CLUB, 25)
    TT = Vector(sc["TABLE_TOP"]); key_matrix(pile10, t, Matrix.Translation(TT)); show(pile10, t)
    def fr(f, u):
        k = ease(u)
        sing.stand(f, SING_CLUB, 25); sing.spine(f, flex=8, pitch=18 - 6 * k, turn=6 * k); sing.eyes(f, pitch=16 - 4 * k, yaw=4)
        sing.jaw(f, 1.0 * k)
        for s in "LR": sing.hang(s, f)
    track(t, L, 4, fr)
    c = cam("CAM_S17", 40, 10); catch(c)
    sc.frame_set(t + L // 2); e = eyes_pt(sing); tgt = TT.lerp(e, 0.5)
    look(c, t, tgt + Vector((0.75, -1.15, 0.05)), tgt)
    look(c, t + L, tgt + Vector((0.62, -0.98, 0.05)), tgt)
    mark("S17", c)

def S18(t, L):
    """'for the rest of his life': his left hand comes to rest flat on the breast pocket (hand on heart), a small nod"""
    begin(ALL, t); park(t, keep=(sing,)); base(sing, t, SING_CLUB, 0)
    def fr(f, u):
        k = ease(u / 0.4) * (1 - ease((u - 0.8) / 0.2))
        sing.stand(f, SING_CLUB, 0); sing.spine(f, flex=-2, pitch=6 * math.sin(u * 4) * k, turn=4); sing.eyes(f, pitch=-2)
        sc.frame_set(f)
        pk = O["Singer.pocketsquare"].matrix_world.translation + Vector((0.0, -0.01, -0.07))
        sh = bone_w(sing, "upperarm01.L")
        if k < 0.05: sing.hang("L", f)
        else:
            rest = sh + Vector((0.06, -0.10, -0.48))
            place_hand(sing.o, "L", f, rest.lerp(pk, k), Vector((0, 1, 0)), Vector((-0.75, 0.0, 0.5)), skin=0.016)
        sing.hang("R", f)
    track(t, L, 3, fr)
    apply_pose(sing.o, "L", "relaxed", t); apply_pose(sing.o, "L", "flat_palm", t + int(0.4 * L)); apply_pose(sing.o, "L", "relaxed", t + L)
    c = cam("CAM_S18", 38, 8); catch(c)
    look(c, t, (CX - 1.55, -2.05, 1.48), (CX - 0.02, -0.12, 1.36))
    look(c, t + L, (CX - 1.30, -1.75, 1.50), (CX - 0.02, -0.12, 1.40))
    mark("S18", c)

# ============================================================================================ CEMETERY
MX = SX["CEMET"]; DAU = (MX + 0.15, 0.78)
def S19(t, L):
    """'And when he was buried': wide, the casket with its flower spray; his daughter walks up to it"""
    begin(ALL, t); park(t, keep=(dau,))
    A = Vector((MX + 1.7, 0.95, 0)); B_ = Vector((DAU[0], DAU[1], 0))
    f1 = t + int(0.8 * L)
    base(dau, t, (A.x, A.y), 90 - 180)
    dau.h.walk(lambda f: A.lerp(B_, (f - t) / (f1 - t)), lambda f: -90 + 70 * ease((f - t) / (f1 - t) * 1.5 - 0.5), t, f1, stride=0.55, step=2)
    def fr(f, u):
        if f <= f1:
            for s in "LR":
                ph = (f - t) / 60 * 2 * math.pi * 0.9 + (0 if s == "L" else math.pi)
                dau.hang(s, f, fwd=0.08 * math.sin(ph), out=0.02)
        else:
            dau.stand(f, DAU, -15); dau.spine(f, pitch=12); dau.eyes(f, pitch=10)
            for s in "LR": dau.hang(s, f)
    track(t, L, 2, fr)
    c = cam("CAM_S19", 30, 8); catch(c, energy=1.0)
    look(c, t, (MX - 1.0, -3.0, 1.6), (MX + 0.5, 0.5, 1.0))
    look(c, t + L, (MX - 0.8, -2.6, 1.6), (MX + 0.3, 0.5, 1.05))
    mark("S19", c)

def S20(t, L):
    """'his daughter': MCU, she stands at the casket, hands folded low, looking down; a slow breath"""
    begin(ALL, t); park(t, keep=(dau,)); base(dau, t, DAU, -15)
    def fr(f, u):
        dau.stand(f, DAU, -15); dau.spine(f, flex=5 + 2 * math.sin(u * 3), pitch=18 + 4 * ease(u), turn=-3); dau.eyes(f, pitch=14)
        for s in "LR": dau.hang(s, f, fwd=0.10, out=-0.06, lift=0.05)
    track(t, L, 4, fr)
    c = cam("CAM_S20", 50, 9); catch(c)
    sc.frame_set(t + L // 2); e = eyes_pt(dau)
    look(c, t, e + Vector((1.15, -0.50, -0.02)), e + Vector((0, 0, -0.16)))
    look(c, t + L, e + Vector((1.00, -0.42, -0.02)), e + Vector((0, 0, -0.14)))
    mark("S20", c)

LIDZ = 0.62 + 0.45 + 0.06
def S21(t, L):
    """'to place ten dimes in his pocket': the ten dimes lying on the closed casket lid by the flowers; she stands behind (no hands)"""
    begin(ALL, t); park(t, keep=(dau, pileD)); base(dau, t, DAU, -15)
    LAND = Vector((MX + 0.42, 0.06, LIDZ + 0.004))
    key_matrix(pileD, t, Matrix.Translation(LAND)); show(pileD, t)
    def fr(f, u):
        dau.stand(f, DAU, -15); dau.spine(f, flex=5, pitch=20 + 3 * math.sin(u * 2)); dau.eyes(f, pitch=16)
        for s in "LR": dau.hang(s, f, fwd=0.10, out=-0.06, lift=0.05)
    track(t, L, 4, fr)
    c = cam("CAM_S21", 45, 11); catch(c, energy=1.0)
    look(c, t, LAND + Vector((0.55, -0.85, 0.42)), LAND + Vector((-0.08, 0.30, 0.25)))
    look(c, t + L, LAND + Vector((0.42, -0.65, 0.33)), LAND + Vector((-0.08, 0.25, 0.20)))
    mark("S21", c)

def S22(t, L):
    """'for him': closing wide push-in, the dimes on the lid, flowers, the daughter standing with folded hands"""
    begin(ALL, t); park(t, keep=(dau, pileD)); base(dau, t, DAU, -10)
    key_matrix(pileD, t, Matrix.Translation(Vector((MX + 0.42, 0.06, LIDZ + 0.008)))); show(pileD, t)
    def fr(f, u):
        dau.spine(f, flex=4, pitch=14 + 3 * math.sin(u * 2), side=1.5 * math.sin(u * 2)); dau.eyes(f, pitch=12)
        for s in "LR": dau.hang(s, f, fwd=0.10, out=-0.06, lift=0.05)
    track(t, L, 4, fr)
    c = cam("CAM_S22", 32, 9); catch(c)
    look(c, t, (MX + 1.9, -2.6, 1.75), (MX + 0.3, 0.3, 1.05))
    look(c, t + L, (MX + 1.4, -2.0, 1.6), (MX + 0.35, 0.25, 1.05))
    mark("S22", c)

def grip(rig, side, t, obj, contact, approach, extra=0.018, **kw):
    a = Vector(approach).normalized()
    return grip_object(rig, side, t, obj, Vector(contact) - a * extra, a, **kw)

only = os.environ.get("ONLY", "")
for k, _ in SHOTS:
    if only and k not in only.split(","): continue
    t0, t1 = T[k]; L = CLIP[k]
    print("BUILD", k, t0, t1, L); sys.stdout.flush()
    globals()[k](t0, L)

cuts = sorted(v[0] for v in T.values())
for o in ALL + list(cams.objects):
    for fc in all_fcurves(o):
        for kp in fc.keyframe_points:
            if any(abs(kp.co.x - (c - 1)) < 0.01 for c in cuts): kp.interpolation = 'CONSTANT'
sc.camera = O["CAM_S01"]
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'; sc.render.use_motion_blur = False
sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
json.dump({k: list(v) for k, v in T.items()}, open(BUILD + "/timing_used.json", "w"))
bpy.ops.wm.save_as_mainfile(filepath=BUILD + "/anim.blend")
print("ANIM saved", FEND)
