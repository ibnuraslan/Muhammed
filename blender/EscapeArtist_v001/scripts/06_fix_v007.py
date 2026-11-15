"""v007 fixes from the moving-preview review (director, 2026-11-14).
blender -b film_look17.blend --python 06_fix_v007.py -- out.blend
Runs on the finished v006b build (animation + look + AimFix). Beat frames unchanged, no VO."""
import sys, math, re
import bpy
from mathutils import Vector, Matrix, Quaternion
HERE = "/home/user/Muhammed/blender/"
exec(open(HERE + "pipeline/anim_lib.py").read())
exec(open(HERE + "EscapeArtist_v001/scripts/escape_lib.py").read())
OUT = sys.argv[sys.argv.index("--") + 1]
O = bpy.data.objects
PR = O["Prisoner"]
P_ = Human(Rig(PR))
ZP = P_.root_head.z

def log(*a): print("FIX", *a, flush=True)

# ------------------------------------------------------------------ hand geometry helpers
def bw(rig, n, tail=False):
    pb = rig.pose.bones[n]; return rig.matrix_world @ (pb.tail if tail else pb.head)
def hand_frame(rig, s):
    """palm centre, palm normal (toward the palm side), finger dir, knuckle axis (index side) in world"""
    wr = bw(rig, "wrist." + s); k3 = bw(rig, "finger3-1." + s)
    k2 = bw(rig, "finger2-1." + s); k5 = bw(rig, "finger5-1." + s)
    d = (k3 - wr).normalized(); a = (k2 - k5).normalized()
    n = d.cross(a) if s == "L" else a.cross(d)
    # orient n to the palm side: curled middle fingertip lies on the palm side
    tip = bw(rig, "finger3-3." + s, tail=True); mid = bw(rig, "finger3-2." + s)
    if ((tip + mid) * 0.5 - k3).dot(n) < 0: n = -n
    palm = wr.lerp(k3, 0.62)
    return palm, n.normalized(), d, a
def fist_point(rig, s):
    """centre of the closed fist ring (where a handle sits)"""
    pts = [bw(rig, "finger%d-1.%s" % (k, s)) for k in (2, 3, 4, 5)] + [bw(rig, "finger%d-2.%s" % (k, s)) for k in (2, 3, 4, 5)] + \
          [bw(rig, "finger%d-3.%s" % (k, s), tail=True) for k in (3, 4)]
    c = Vector()
    for p in pts: c += p
    return c / len(pts)
def pinch_point(rig, s):
    return (bw(rig, "finger1-3." + s, tail=True) + bw(rig, "finger2-3." + s, tail=True)) * 0.5

def obj_local_axis(o):
    """longest bbox axis of a mesh (including mesh children) in o's local space, and the bbox centre"""
    pts = []
    for c in [o] + list(o.children_recursive):
        if c.type != "MESH": continue
        M = o.matrix_world.inverted() @ c.matrix_world
        pts += [M @ Vector(v) for v in c.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    ext = hi - lo; ax = max(range(3), key=lambda i: ext[i])
    v = Vector((0, 0, 0)); v[ax] = 1
    return v, (lo + hi) * 0.5, ext

def key_matrix(o, f, M):
    o.parent = None; o.matrix_world = M
    o.keyframe_insert("location", frame=f); o.rotation_mode = "XYZ"; o.keyframe_insert("rotation_euler", frame=f)

def align(local_axis, world_axis, local_up=None, world_up=None):
    """rotation taking local_axis -> world_axis (and roughly local_up -> world_up)"""
    q = local_axis.rotation_difference(world_axis)
    if local_up is not None and world_up is not None:
        u = q @ local_up; wu = world_up - world_axis * world_up.dot(world_axis)
        u = u - world_axis * u.dot(world_axis)
        if u.length > 1e-6 and wu.length > 1e-6:
            ang = u.normalized().angle(wu.normalized())
            sgn = 1 if u.normalized().cross(wu.normalized()).dot(world_axis) >= 0 else -1
            q = Quaternion(world_axis, sgn * ang) @ q
    return q.to_matrix().to_4x4()

def clear_tf(o, f0, f1):
    for fc in fcurves_of(o):
        if fc.data_path in ("location", "rotation_euler", "rotation_quaternion"):
            for k in [k for k in fc.keyframe_points if f0 <= k.co.x <= f1][::-1]:
                fc.keyframe_points.remove(k)

def clear_hand(rig, s, f0, f1):
    clear_keys(rig, f0, f1, 'IK_hand.' + s)
    for bn in [b.name for b in rig.pose.bones if (b.name.startswith("finger") or b.name.startswith("metacarpal")) and b.name.endswith("." + s)]:
        clear_keys(rig, f0, f1, 'bones["%s"]' % bn)
def clear_fingers(rig, s, f0, f1):
    for bn in [b.name for b in rig.pose.bones if b.name.startswith("finger") and b.name.endswith("." + s)]:
        clear_keys(rig, f0, f1, 'bones["%s"]' % bn)

def bake_in_fist(o, rig, s, f0, f1, step=2, flip=False, grip_frac=0.5, grip_local=None, handle_ref=None, up_axis=None):
    """the object's long axis runs through the fist along the knuckle line; the point at grip_frac along the axis sits in the fist.
    handle_ref=(frame, world point): the axis end nearest that point is the handle end (grip_frac counts from it).
    grip_local + up_axis: hang the object from grip_local (e.g. a carry handle) with up_axis pointing up the arm."""
    ax, ctr, ext = obj_local_axis(o)
    Sm = Matrix.Diagonal(o.matrix_world.to_scale()).to_4x4()
    if handle_ref is not None:
        sc.frame_set(handle_ref[0]); e0 = o.matrix_world @ (ctr - ax * max(ext) * 0.5); e1 = o.matrix_world @ (ctr + ax * max(ext) * 0.5)
        if (e1 - handle_ref[1]).length < (e0 - handle_ref[1]).length: ax = -ax
    if grip_local is not None:
        for f in list(range(f0, f1 + 1, step)) + [f1]:
            sc.frame_set(f)
            c = fist_point(rig, s); _, n, d, a = hand_frame(rig, s)
            R = align(ax, a, up_axis, -d)
            key_matrix(o, f, Matrix.Translation(c) @ R @ Sm @ Matrix.Translation(-grip_local))
        return
    L = max(ext); g = ctr + ax * (L * (grip_frac - 0.5))
    if flip: ax = -ax
    for f in list(range(f0, f1 + 1, step)) + [f1]:
        sc.frame_set(f)
        c = fist_point(rig, s); _, n, d, a = hand_frame(rig, s)
        R = align(ax, a, up_axis if up_axis is not None else (Vector((0, 0, 1)) if ax.z == 0 else Vector((1, 0, 0))), -d)
        M = Matrix.Translation(c) @ R @ Sm @ Matrix.Translation(-g)
        key_matrix(o, f, M)

def bake_in_pinch(o, rig, s, f0, f1, step=2, out=0.6):
    """flat small object between thumb and index tips, sticking out of the fingers along the finger direction"""
    ax, ctr, ext = obj_local_axis(o)
    Sm = Matrix.Diagonal(o.matrix_world.to_scale()).to_4x4()
    L = max(ext); g = ctr - ax * (L * (out - 0.5))
    for f in list(range(f0, f1 + 1, step)) + [f1]:
        sc.frame_set(f)
        c = pinch_point(rig, s); _, n, d, a = hand_frame(rig, s)
        R = align(ax, d, Vector((0, 0, 1)) if ax.z == 0 else Vector((1, 0, 0)), n)
        key_matrix(o, f, Matrix.Translation(c) @ R @ Sm @ Matrix.Translation(-g))

def snap_hand(rig, s, f, target, point_fn, iters=3):
    """shift IK_hand.<s> at frame f so point_fn(rig, s) lands on target"""
    pb = rig.pose.bones["IK_hand." + s]
    for _ in range(iters):
        sc.frame_set(f)
        dlt = target - point_fn(rig, s)
        if dlt.length < 0.004: break
        Mw = rig.matrix_world @ pb.matrix
        Mw = Matrix.Translation(dlt) @ Mw
        pb.matrix = rig.matrix_world.inverted() @ Mw
        pb.keyframe_insert("location", frame=f, group=pb.name)

def pose_fingers(rig, s, name, frames, amount=1.0):
    rot = _pose_rots(rig, s, name)
    for f in frames: _key(rig, s, rot, f, amount)

# ------------------------------------------------------------------ 1. camera: no DOF blur anywhere; no floating key overlay
cam = sc.camera
# DOF stays on at f/11 (director): no visible blur at these distances, but not the flat all-sharp look
for fc in fcurves_of(cam.data):
    if "aperture_fstop" in fc.data_path:
        for k in list(fc.keyframe_points)[::-1]: fc.keyframe_points.remove(k)
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 11.0
kg = O["KeyGlow"]
if kg.animation_data: kg.animation_data_clear()
kg.hide_render = True; kg.hide_viewport = True; kg.location = (0, 0, -100)
log("dof f/11, KeyGlow removed")

# ------------------------------------------------------------------ 2. camera path edits (re-built from the 03_animate key list)
src = open(HERE + "EscapeArtist_v001/scripts/03_animate.py").read()
CK = eval(re.search(r"\nCK = (\[.*?\n\])\nbuild_camera", src, re.S).group(1))
CKd = {k[0]: k for k in CK}
EDIT = {
    # beat 1: high corner instead of the guard's back filling the lens
    45:  (45,  (1.7, 2.45, 2.35), (3.1, 1.2, 1.05), 24, 0),
    95:  (95,  (0.95, 2.45, 2.3), (1.6, 1.1, 1.0), 22, 0),
    # beat 2: stay on him while he crosses to the bunk; medium shots of the filing (no macro, no dutch)
    276: (276, (-0.95, -1.75, 1.6), (0.22, -1.85, 1.3), 24, 0),     # his profile on the beat frame, turning to camera
    330: (330, (-0.6, -1.05, 1.45), (0.2, -1.85, 0.85), 28, 0),
    390: (390, (-0.55, -1.5, 1.25), (0.2, -1.85, 0.82), 32, 0),
    450: (450, (-0.4, -2.45, 1.3), (0.22, -1.85, 0.85), 32, 0),
    510: (510, (-0.5, -1.6, 1.3), (0.3, -1.85, 1.05), 30, 0),
    535: (535, (-0.45, -1.25, 1.4), (0.45, -1.85, 1.1), 28, 0),
    # beat 3: inside the cell looking at the lock without crossing the bars
    558: (558, (-0.6, -1.2, 1.5), (0.45, -1.8, 1.2), 28, 0),        # in front of him as he stands up (beat 3)
    # beat 4: face the memory room before the wall (wall hidden during the pass)
    690: (690, (0.6, 2.75, 1.5), (0.45, 8.3, 1.0), 24, 0),
    # beat 4: keep the camera off the boy's head (it fills the lens at 850-865)
    830: (830, (1.3, 7.95, 1.4), (0.45, 8.45, 0.95), 38, 0),
    890: (890, (1.75, 7.55, 1.5), (0.8, 8.35, 1.15), 28, 0),
    # beat 7: further back from the gavel (it filled the lens)
    1445: (1445, (9.6, 6.25, 1.5), (10.15, 7.35, 1.2), 40, 0),
    # beat 8: over the fence top above the razor coil (it flew through the outrigger at 1775-1785)
    1785: (1785, (7.6, -14.0, 4.55), (7.0, -14.6, 1.2), 26, 0),
    # beats 14-15: over the fence top both ways above the razor coil (it flew through the outrigger at 3570-3580 and 3630-3635)
    3570: (3570, (0.3, -12.8, 4.9), (0.3, -17.7, 1.4), 35, 0),
    3590: (3590, (0.45, -14.7, 4.7), (0.3, -17.7, 1.4), 32, 0),
    3632: (3632, (0.75, -14.7, 4.7), (0.0, -3.2, 1.75), 28, 0),
}
for k, v in EDIT.items():
    CKd[k] = v
CK2 = [CKd[k] for k in sorted(CKd)]
build_camera(cam, CK2)
for fc in fcurves_of(cam.data):
    if "aperture_fstop" in fc.data_path or "focus_distance" in fc.data_path:
        pass
log("camera rebuilt", len(CK2), "keys")

# no auto-aim during the pass into the memory (it turned the camera back to the corridor)
for c in cam.constraints:
    if not c.name.startswith("AimFix"): continue
    path = 'constraints["%s"].influence' % c.name
    fc = [x for x in fcurves_of(cam) if x.data_path == path]
    v0 = fc[0].evaluate(682) if fc else c.influence; v1 = fc[0].evaluate(716) if fc else c.influence
    if fc:
        for k in [k for k in fc[0].keyframe_points if 682 <= k.co.x <= 716][::-1]: fc[0].keyframe_points.remove(k)
    for f, v in ((682, v0), (689, 0.0), (709, 0.0), (716, v1)):
        c.influence = v; cam.keyframe_insert(path, frame=f)
    log("aim off 689-709", c.name, round(v0, 2), round(v1, 2))
# cell-front bars: hidden for the few frames the camera passes through their plane (no bar filling the lens)
cf = O["CellFront_0"]; cross = []
for f in range(150, 720):
    sc.frame_set(f); p = cam.matrix_world.translation
    if abs(p.y) < 0.12 and -1.45 < p.x < 1.45: cross.append(f)
spans = []
for f in cross:
    if spans and f - spans[-1][1] <= 3: spans[-1][1] = f
    else: spans.append([f, f])
keys = [(-1, False)]
for a_, b_ in spans: keys += [(a_ - 1, True), (b_ + 2, False)]
for f, h in keys:
    cf.hide_render = h; cf.keyframe_insert("hide_render", frame=f); cf.hide_viewport = h; cf.keyframe_insert("hide_viewport", frame=f)
for fc in fcurves_of(cf):
    for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"
log("cell front hidden while the camera crosses it", spans)
# wall the camera passes through on the way into the memory: hidden (render + viewport) for that pass only
wall = O["Corridor_FarWall"]
for f, h in ((-1, False), (682, True), (708, False)):
    wall.hide_render = h; wall.keyframe_insert("hide_render", frame=f)
    wall.hide_viewport = h; wall.keyframe_insert("hide_viewport", frame=f)
for fc in fcurves_of(wall):
    for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"

# ------------------------------------------------------------------ 3. beat 2: file in the right fist, scrap pinched in the left
filev = O["File_Blade"]; scrap = O["ScrapKey"]
clear_fingers(PR, "R", 300, 540); clear_fingers(PR, "L", 300, 540)
pose_fingers(PR, "R", "wrap_grip", range(300, 541, 8))
pose_fingers(PR, "L", "pinch", range(300, 541, 8))
clear_tf(filev, 300, 541)
clear_tf(scrap, 300, 541)
bake_in_fist(filev, PR, "R", 314, 541, grip_frac=0.18)
bake_in_pinch(scrap, PR, "L", 314, 541, out=0.65)
log("beat 2 props baked")

# ------------------------------------------------------------------ 4. beat 3: the key stays in his pinch until it is in the lock, and his pinch is on it in the lock
clear_fingers(PR, "R", 541, 627)
pose_fingers(PR, "R", "pinch", range(541, 628, 6))
clear_tf(scrap, 541, 601)
bake_in_pinch(scrap, PR, "R", 541, 601, out=0.7)
KEYHOLE = Vector((-0.15, -0.055, 1.0))
for f in range(604, 627, 2):
    sc.frame_set(f)
    ax, ctr, ext = obj_local_axis(scrap)
    bow = scrap.matrix_world @ (ctr - ax * (max(ext) * 0.35))     # the key's bow, outside the lock
    snap_hand(PR, "R", f, bow, pinch_point)
log("beat 3 key in pinch")

# ------------------------------------------------------------------ 4b. beat 5: the toolbox hangs from the father's fist, is handed into the boy's fist
FAr = O["Father"]; BOr = O["Boy"]; FA_ = Human(Rig(FAr)); BO_ = Human(Rig(BOr))
tbx = O["Toolbox"]
tbx.scale = tbx.scale * 0.75
tax, tctr, text = obj_local_axis(tbx)
up_l = Vector((0, 0, 1))
sc.frame_set(0)
TB_GRIP = Vector((tctr.x, tctr.y, tctr.z + text.z * 0.5 - 0.01))                  # top of the carry handle, object space
clear_hand(FAr, "R", 990, 1060); clear_hand(FAr, "L", 990, 1060)
def side_hand(rig, H, f, s, fwd=0.0, lift=0.0):
    sc.frame_set(f)
    hR = bw(rig, "upperleg01.R"); hL = bw(rig, "upperleg01.L"); sp = bw(rig, "spine03")
    side = (hR - hL).normalized() * (1 if s == "R" else -1)
    fw = Vector((0, 0, 1)).cross(hR - hL).normalized()
    if (sp - (hR + hL) * 0.5).dot(fw) < -0.5: fw = -fw
    W = (hR if s == "R" else hL) + side * 0.16 + fw * (0.06 + fwd) + Vector((0, 0, 0.02 + lift))
    return W, Vector((0, 0, -1)), -side, W + side * 0.25 + Vector((0, 0, 0.35)) - fw * 0.3
sc.frame_set(990); TB_H0 = tbx.matrix_world @ TB_GRIP
for f in range(990, 1001, 2):             # reach the handle on the floor
    W, d, n, pole = side_hand(FAr, FA_, f, "R")
    FA_.key_hand("R", f, W.lerp(TB_H0 + Vector((0, 0, 0.09)), min(1, (f - 990) / 8)), d, n, pole)
    grip(FA_, "R", f, pose_name="wrap_grip")
# the boy reaches out to receive it, then carries it at his side like his father
clear_hand(BOr, "R", 1036, 1421)
for f in list(range(1036, 1422, 4)):
    if f < 1060:
        u = 1 - abs(f - 1048) / 12.0
        W, d, n, pole = side_hand(BOr, BO_, f, "R", fwd=0.22 * u, lift=0.12 * u)
    else:
        W, d, n, pole = side_hand(BOr, BO_, f, "R")
    BO_.key_hand("R", f, W, d, n, pole)
sc.frame_set(1048); BHAND = fist_point(BOr, "R")
for f in range(1002, 1049, 2):            # carry at his side, then hold it out to the boy
    W, d, n, pole = side_hand(FAr, FA_, f, "R")
    u = max(0.0, (f - 1030) / 18.0)
    FA_.key_hand("R", f, W.lerp(BHAND + Vector((0.04, 0, 0.06)), u), d, n, pole)
    grip(FA_, "R", f, pose_name="wrap_grip")
for f in range(990, 1061, 6):
    W, d, n, pole = side_hand(FAr, FA_, f, "L")
    FA_.key_hand("L", f, W, d, n, pole); grip(FA_, "L", f, pose_name="relaxed")
for f in (1052, 1060):
    W, d, n, pole = side_hand(FAr, FA_, f, "R")
    FA_.key_hand("R", f, W, d, n, pole); grip(FA_, "R", f, pose_name="relaxed")
clear_fingers(BOr, "R", 1036, 1421); pose_fingers(BOr, "R", "wrap_grip", range(1036, 1422, 8))
clear_tf(tbx, 992, 1421)
bake_in_fist(tbx, FAr, "R", 1001, 1047, grip_local=TB_GRIP, up_axis=up_l)
bake_in_fist(tbx, BOr, "R", 1048, 1421, grip_local=TB_GRIP, up_axis=up_l)
log("toolbox handed over fist to fist")

# ------------------------------------------------------------------ 4c. beat 6: stepmother's pointing arm bends (was locked straight out)
SMr = O["Stepmother"]; SM_ = Human(Rig(SMr))
SR = Vector((7.2, 8.3, SM_.root_head.z)); SYw = -35
for f in range(1140, 1422, 4):
    t = (f - 1140) / 60; pt = 0.5 + 0.5 * math.sin(t * 5)
    dL, nL = hand_dirs(SYw, (-0.4, 1, 0.2), (0, 0, -1))
    SM_.key_hand("L", f, rel(SR, SYw, (-0.3, 0.36 + 0.05 * pt, 0.36)), dL, nL, rel(SR, SYw, (-0.55, -0.25, 0.05)))
log("stepmother elbow bent")

# ------------------------------------------------------------------ 4d. beat 7: the gavel is in the judge's fist; the fist does the strike
JUr = O["Judge"]; JU_ = Human(Rig(JUr)); gav = O["Gavel"]
gpiv = Vector((10.2, 7.48, 1.2)); JY = 0
strike = [(1380, 0.0), (1415, -0.9), (1432, -1.1), (1440, 0.03), (1446, -0.12), (1452, 0.0), (1470, -0.7), (1478, 0.02), (1500, 0.0)]
SPk = catmull([(f, a) for f, a in strike])
clear_hand(JUr, "R", 1380, 1547)
for f in range(1380, 1548, 2):
    a = max(0.0, -SPk(f))
    hp = gpiv + Vector((0, 0.1, 0.06)) + Vector((0, 0.06 * a, 0.2 * a))
    dR, nR = hand_dirs(JY, (0, -0.25 + 0.5 * a, -1 + 0.6 * a), (1, 0, 0))     # hammer grip: fingers round the handle, thumb toward the block
    JU_.key_hand("R", f, hp, dR, nR, JUr.matrix_world @ Vector((10.6, 7.9, 1.0)) if False else Vector((10.6, 7.95, 1.0)))
pose_fingers(JUr, "R", "wrap_grip", range(1380, 1548, 8))
clear_tf(gav, 1380, 1547)
gax, _, _ = obj_local_axis(gav)
GHEAD = Vector((0, 1, 0)) if abs(gax.x) > 0.5 else Vector((1, 0, 0))     # the head's cylinder axis (neither the handle nor the lying-flat up)
bake_in_fist(gav, JUr, "R", 1380, 1547, grip_frac=0.12, handle_ref=(0, gpiv), up_axis=GHEAD)
log("gavel in the judge's fist")

# ------------------------------------------------------------------ 5. beat 8: fence climb off the mesh, over the top on a blanket, drop
FX = 7.0; M_Y = -13.8; TOP = 3.6
# a blanket thrown over the razor wire where he crosses; the wire under it is cut away
rw = O["RazorWire_Top"]
me = rw.data; Mw = rw.matrix_world
import bmesh
bm = bmesh.new(); bm.from_mesh(me)
dead = [v for v in bm.verts if abs((Mw @ v.co).x - FX) < 0.62]
bmesh.ops.delete(bm, geom=dead, context="VERTS"); bm.to_mesh(me); bm.free()
LT = 3.1; OY = -14.18; OZ = 3.58                # chain-link top rail (y = M_Y) and the outrigger end
def out_z(y): return LT + (M_Y - y) / (M_Y - OY) * (OZ - LT)
prof = [(M_Y + 0.1, 2.88), (M_Y + 0.025, 3.13), (M_Y - 0.1, out_z(M_Y - 0.1) + 0.035), (M_Y - 0.24, out_z(M_Y - 0.24) + 0.035),
        (OY + 0.0, OZ + 0.04), (OY - 0.05, OZ - 0.04)]
vs, fs = [], []
NX = 9
for i in range(NX):
    x = FX - 0.45 + 0.9 * i / (NX - 1)
    for j, (y, z) in enumerate(prof):
        wob = 0.012 * math.sin(i * 1.7 + j * 2.3) + 0.03 * (j in (0, len(prof) - 1)) * math.sin(i * 2.9)
        vs.append((x, y + wob * 0.5, z + wob))
for i in range(NX - 1):
    for j in range(len(prof) - 1):
        a = i * len(prof) + j; fs.append((a, a + 1, a + 1 + len(prof), a + len(prof)))
bme = bpy.data.meshes.new("Blanket"); bme.from_pydata(vs, [], fs); bme.update()
bl = bpy.data.objects.new("Blanket", bme); sc.collection.objects.link(bl)
for p in bme.polygons: p.use_smooth = True
bm_ = bpy.data.materials.new("BlanketWool"); bm_.use_nodes = True
bsd = bm_.node_tree.nodes["Principled BSDF"]; bsd.inputs["Base Color"].default_value = (0.07, 0.055, 0.045, 1); bsd.inputs["Roughness"].default_value = 0.95
bme.materials.append(bm_)
vis_key([bl], [(1548, 1860)])

R_FROM = 1600
clear_keys(PR, R_FROM + 1, 1791)
def climb_key(f, root, yaw, flex, head, hL, hR, fL, fR, pole_side=True, fpitch=-30):
    P_.key_root(f, root, yaw=yaw, flex=flex)
    P_.key_spine(f, flex=flex * 0.6, head=head)
    dd, nn = hand_dirs(yaw, (0, 0.2, 1), (0, 1, 0))
    for s, W, F in (("L", hL, fL), ("R", hR, fR)):
        sx = -1 if s == "L" else 1
        P_.key_hand(s, f, W, dd, nn, root + Vector((sx * 0.6, 0.3, 0.1)))
        P_.r.key_world("IK_foot." + s, f, Matrix.Translation(F) @ Matrix.Rotation(R_(yaw), 4, "Z") @ Matrix.Rotation(R_(fpitch), 4, "X") @
                       Matrix.Translation(-P_.ankle[s]) @ P_.r.rest("IK_foot." + s))
        pb = P_.r.PB["Pole_knee." + s]; pn = "Pole_knee." + s
        pk = root + (Vector((sx * 0.65, -0.25, -0.45)) if pole_side else Vector((sx * 0.3, -0.6, -0.4)))
        pb.location = P_.r.rest(pn).to_3x3().inverted() @ (pk - P_.r.BN[pn].head_local); pb.keyframe_insert("location", frame=f)

RZ0 = ZP; RZ1 = 2.5                      # climb: pelvis up to 2.5 m (hands stay on the chain-link below its top rail)
for f in range(1600, 1701, 4):
    u = (f - 1600) / 100.0
    rz = RZ0 + (RZ1 - RZ0) * u
    ph = (f - 1600) / 20.0; a = (ph % 2) < 1
    hz = min(LT - 0.06, rz + 0.5)
    hL = Vector((FX - 0.22, M_Y + 0.1, hz + (0.0 if a else -0.14)))
    hR = Vector((FX + 0.22, M_Y + 0.1, hz + (-0.14 if a else 0.0)))
    fL = Vector((FX - 0.17, M_Y + 0.24, rz - 0.82 + (0.0 if a else 0.16)))
    fR = Vector((FX + 0.17, M_Y + 0.24, rz - 0.82 + (0.16 if a else 0.0)))
    climb_key(f, Vector((FX, M_Y + 0.52, rz)), 0, 4, (-18, 0), hL, hR, fL, fR)
    face(P_, f, brow=-1.0, lid=0.4, jaw=10, frown=0.6)
# hoist over the top rail onto the blanket, swing the legs over the outrigger, sit on the edge facing out, jump
seq = [
    (1706, (M_Y + 0.42, 2.85), 12, (-10, 0), ((M_Y + 0.02, 3.14), (M_Y + 0.02, 3.14)), (M_Y + 0.24, 2.05), (M_Y + 0.24, 2.2)),
    (1713, (M_Y + 0.32, 3.25), 22, (0, 0), ((M_Y - 0.06, 3.27), (M_Y - 0.06, 3.27)), (M_Y + 0.24, 2.4), (M_Y + 0.24, 2.55)),
    (1720, (M_Y + 0.14, 3.72), 28, (0, 0), ((M_Y - 0.2, 3.45), (M_Y - 0.2, 3.45)), (M_Y + 0.26, 2.75), (M_Y + 0.2, 3.38)),
    (1727, (M_Y - 0.05, 3.96), 22, (0, 0), ((M_Y - 0.28, 3.53), (M_Y - 0.28, 3.53)), (M_Y + 0.2, 3.45), (M_Y - 0.15, 4.08)),
    (1734, (M_Y - 0.25, 3.94), 12, (0, 0), ((M_Y - 0.2, 3.46), (M_Y - 0.2, 3.46)), (M_Y - 0.1, 4.08), (OY - 0.25, 3.2)),
    (1741, (OY - 0.06, 3.82), 8, (-8, 0), ((OY + 0.02, 3.63), (OY + 0.02, 3.63)), (OY - 0.25, 2.95), (OY - 0.25, 2.92)),
]
for f, rt, flex, head, hz, fl, fr in seq:
    root = Vector((FX, rt[0], rt[1]))
    hL = Vector((FX - 0.28, hz[0][0], hz[0][1])); hR = Vector((FX + 0.28, hz[1][0], hz[1][1]))
    fL = Vector((FX - 0.17, fl[0], fl[1])); fR = Vector((FX + 0.17, fr[0], fr[1]))
    climb_key(f, root, 0, flex, head, hL, hR, fL, fR, fpitch=-10)
    face(P_, f, brow=-1.0, lid=0.4, jaw=12, frown=0.7)
# jump: free fall from the edge, forward and away from the fence (g = 9.8 m/s^2), landing in the existing crouch at 1792
g = 9.8; z0 = 3.82; zl = ground_z(FX, M_Y - 0.6) + ZP - 0.38
T = math.sqrt(2 * (z0 - zl) / g); fl_ = int(round(T * 60)); t0 = max(1743, 1792 - fl_)
log("drop frames", fl_, "t0", t0)
for f in list(range(t0, 1790, 3)) + [1790]:
    t = (f - t0) / 60.0; z = max(zl, z0 - 0.5 * g * t * t); y = OY - 0.06 - min(1.0, t / T) * 0.3
    root = Vector((FX, y, z))
    hL = root + Vector((-0.38, -0.12, 0.35)); hR = root + Vector((0.38, -0.12, 0.35))
    fL = root + Vector((-0.15, -0.1, -0.85)); fR = root + Vector((0.15, -0.04, -0.82))
    climb_key(f, root, 0, 8, (-5, 0), hL, hR, fL, fR, fpitch=0)
# grips: hands on the chain-link while climbing, on the blanket over the top
for f in range(1600, 1701, 4):
    for s_ in "LR":
        sc.frame_set(f); W_ = bw(PR, "wrist." + s_)
        gripo(P_, s_, f, O["Object_8"], Vector((W_.x, M_Y + 0.012, W_.z + 0.06)), (0, -1, 0), finger_dir=(0, 0, -1))
for f in range(1706, 1742, 7):
    for s_ in "LR": grip(P_, s_, f, pose_name="flat_palm" if f >= 1720 else "wrap_grip")
for f in (1752, 1772, 1788):
    for s_ in "LR": grip(P_, s_, f, pose_name="relaxed")
log("fence re-staged")

# ------------------------------------------------------------------ 6. beat 10: one-handed diagonal saw stroke between the bars; left hand off the bars
saw = O["Hacksaw"]; barp = Vector((0.0, -3.2, 1.62))
AX = Vector((1, -1, 0)).normalized()          # handle toward the cell, blade across bar 2
clear_hand(PR, "R", 2187, 2440); clear_hand(PR, "L", 2187, 2440)
clear_tf(saw, 2187, 2441)
SWR = Vector((0.05, -2.55, ZP + 0.03))
sax, sctr, sext = obj_local_axis(saw)
for f in range(2187, 2441, 3):
    st = math.sin((f - 2186) * 2 * math.pi / 26)
    sp = barp + Vector((0, 0.025, 0)) + AX * (0.05 * st)
    handle = sp - AX * 0.13
    dR, nR = hand_dirs(0, (-0.5, -1, -0.2), (0, 0, -1))
    P_.key_hand("R", f, handle + Vector((0.03, 0.09, 0.03)), dR, nR, SWR + Vector((0.55, 0.2, 0.3)))
    # left hand braced on the wall beside the window
    dL, nL = hand_dirs(0, (0, -0.2, 1), (0, -1, 0))
    P_.key_hand("L", f, Vector((0.45, -3.02, 1.45)), dL, nL, SWR + Vector((0.6, 0.25, 0.1)))
pose_fingers(PR, "R", "wrap_grip", range(2187, 2441, 6))
pose_fingers(PR, "L", "flat_palm", range(2187, 2441, 12))
for f in range(2187, 2441, 3):
    st = math.sin((f - 2186) * 2 * math.pi / 26)
    sp = barp + Vector((0, 0.025, 0)) + AX * (0.05 * st)
    handle = sp - AX * 0.13
    snap_hand(PR, "R", f, handle, fist_point, iters=2)
bake_in_fist(saw, PR, "R", 2187, 2440, step=3, grip_frac=0.1)
log("saw re-staged")

# ------------------------------------------------------------------ 7. beat 11: the bent tube in his right fist
tube = O["ToothpasteTube"]
clear_tf(tube, 2566, 2898)
clear_fingers(PR, "R", 2566, 2898)
pose_fingers(PR, "R", "wrap_grip", range(2566, 2899, 8))
bake_in_fist(tube, PR, "R", 2566, 2898, grip_frac=0.3)
log("tube in fist")

sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
log("SAVED", OUT)
