# EscapeArtist helpers, exec'd after blender/pipeline/anim_lib.py (Rig, Human, make_human_ctrl, catmull, smooth, ev).
import math, bpy
from mathutils import Vector, Matrix, Quaternion, Euler
from mathutils.bvhtree import BVHTree
R_ = math.radians
sc = bpy.context.scene
FPS = 60

# ---------------------------------------------------------------- ground: z=0 indoors, ray against the displaced yard outdoors
_GB = {}
def _bvh(name):
    if name not in _GB:
        o = bpy.data.objects[name]; dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg)
        me = e.to_mesh(); M = o.matrix_world
        _GB[name] = BVHTree.FromPolygons([M @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
        e.to_mesh_clear()
    return _GB[name]
def ground_z(x, y):
    if y < -3.5:
        hit = _bvh("Yard_Ground").ray_cast(Vector((x, y, 5.0)), Vector((0, 0, -1)))
        return hit[0].z if hit[0] else 0.0
    return 0.0
globals()["ground_z"] = ground_z

# ---------------------------------------------------------------- visibility: key hide_render on a set of objects
def vis_key(objs, ranges, f_end=3750):
    """ranges: list of (f0, f1) visible. Constant interpolation."""
    for o in objs:
        vp = False                    # viewport stays on so hidden props keep evaluating (they are parked instead)
        o.hide_render = True; o.keyframe_insert("hide_render", frame=-1)
        if vp: o.hide_viewport = True; o.keyframe_insert("hide_viewport", frame=-1)
        for f0, f1 in ranges:
            o.hide_render = False; o.keyframe_insert("hide_render", frame=f0)
            o.hide_render = True; o.keyframe_insert("hide_render", frame=f1 + 1)
            if vp:
                o.hide_viewport = False; o.keyframe_insert("hide_viewport", frame=f0)
                o.hide_viewport = True; o.keyframe_insert("hide_viewport", frame=f1 + 1)
        o.hide_render = not any(f0 <= 0 <= f1 for f0, f1 in ranges)
        if o.animation_data and o.animation_data.action:
            for fc in fcurves_of(o):
                for k in fc.keyframe_points: k.interpolation = "CONSTANT"
        if vp: o.hide_viewport = o.hide_render
        # props (not characters): park far below the set while hidden, so nothing invisible sits next to a hand
        if o.parent is None and o.type != "ARMATURE":
            o.delta_location = (0, 0, -100); o.keyframe_insert("delta_location", frame=-1)
            for f0, f1 in ranges:
                o.delta_location = (0, 0, 0); o.keyframe_insert("delta_location", frame=f0)
                o.delta_location = (0, 0, -100); o.keyframe_insert("delta_location", frame=f1 + 1)
            for fc in fcurves_of(o):
                if fc.data_path == "delta_location":
                    for k in fc.keyframe_points: k.interpolation = "CONSTANT"
            o.delta_location = (0, 0, 0 if any(f0 <= 0 <= f1 for f0, f1 in ranges) else -100)

def fcurves_of(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    act = ad.action
    try:
        return list(act.fcurves)
    except AttributeError:
        out = []
        for layer in act.layers:
            for strip in layer.strips:
                for cb in strip.channelbags: out += list(cb.fcurves)
        return out

def human_objs(name):
    return [o for o in bpy.data.objects if o.name == name or (o.parent and o.parent.name == name)]

# ---------------------------------------------------------------- fingers & face
FING = ["finger%d-%d" % (a, b) for a in range(1, 6) for b in range(1, 4)]
def grip(H, s, f, amt=1.0, thumb=0.7, spread=0.0):
    """curl all fingers (0 open .. 1 fist). Bends about local X."""
    for a in range(1, 6):
        for b in range(1, 4):
            n = "finger%d-%d.%s" % (a, b, s)
            if n not in H.r.PB: continue
            ang = (thumb * 35 if a == 1 else 75 if b == 1 else 85 if b == 2 else 55) * (amt if a > 1 else thumb)
            sp = spread * (a - 3) * 6
            H.r.key_q(n, f, Quaternion((1, 0, 0), R_(ang)) @ Quaternion((0, 0, 1), R_(sp if b == 1 else 0)))

FACE = None
def face(H, f, brow=0.0, lid=0.0, jaw=0.0, smile=0.0, frown=0.0):
    """brow: +up/-down(furrow); lid: 0 open .. 1 shut; jaw: open deg; smile/frown 0..1. Uses MPFB default-rig face bones."""
    P = H.r.PB
    def rot(n, ax, d):
        if n in P: H.r.key_q(n, f, Quaternion(ax, R_(d)))
    rot("jaw", (1, 0, 0), jaw)
    for s, sg in (("L", 1), ("R", -1)):
        rot("oculi01." + s, (1, 0, 0), -brow * 14)
        rot("oculi02." + s, (1, 0, 0), -brow * 10)
        rot("orbicularis03." + s, (1, 0, 0), lid * 28)
        rot("orbicularis04." + s, (1, 0, 0), -lid * 10)
        rot("risorius03." + s, (0, 0, 1), sg * (smile * 18 - frown * 12))
        rot("risorius02." + s, (1, 0, 0), -smile * 10 + frown * 10)
        rot("levator06." + s, (1, 0, 0), -smile * 6 - frown * 6)

# ---------------------------------------------------------------- generic pose helper
def pose(H, f, root, yaw=0.0, flex=0.0, side=0.0, feet=None, spine=(0, 0, 0), head=(0, 0), hands=None, fingers=None):
    """root: Vector root-bone head position. feet: {'L': (xy, yaw, lift, pitch)}; default: under hips.
    hands: {'L': (W, d, n, pole)}. fingers: {'L': amt}."""
    H.key_root(f, Vector(root), yaw=yaw, flex=flex, side=side)
    H.key_spine(f, flex=spine[0], twist=spine[1], side=spine[2], head=head)
    for s in "LR":
        if feet and s in feet:
            ft = feet[s]; xy = Vector(ft[0]); H.key_foot(s, f, xy, ft[1], ft[2] if len(ft) > 2 else 0.0, ft[3] if len(ft) > 3 else 0.0)
        else:
            H.key_foot(s, f, H.foot_xy(s, Vector(root), yaw), yaw)
        if hands and s in hands:
            W, d, n, pl = hands[s]
            if pl is None: pl = rel(root, yaw + spine[1], ((1 if s == "R" else -1) * 0.5, -0.45, 0.25))
            H.key_hand(s, f, Vector(W), Vector(d), Vector(n), Vector(pl))
        else:
            # relaxed arm hanging at the side, elbow pole behind
            W = rel(root, yaw + spine[1], ((1 if s == "R" else -1) * 0.31, 0.04, -0.06)); d, n = hand_dirs(yaw, (0, 0.15, -1), ((1 if s == "R" else -1) * -1, 0, 0))
            H.key_hand(s, f, W, d, n, rel(root, yaw, ((1 if s == "R" else -1) * 0.5, -0.45, 0.25)))
            if not (fingers and s in fingers): grip(H, s, f, 0.3, 0.3)
        if fingers and s in fingers:
            v = fingers[s]
            if isinstance(v, str): grip(H, s, f, pose_name=v)
            else: grip(H, s, f, v)

def yawv(deg):
    """unit facing vector for yaw deg (MPFB faces -Y at yaw 0)"""
    return Vector((math.sin(R_(deg)), -math.cos(R_(deg)), 0))

def rel(root, yaw, v):
    """point given in character space (x right, y forward, z up) -> world"""
    fw = yawv(yaw); rt = Vector((-fw.y, fw.x, 0)) * -1
    return Vector(root) + rt * v[0] + fw * v[1] + Vector((0, 0, v[2]))

def hand_dirs(yaw, fwd=(0, 1, 0), palm=(0, 0, -1)):
    """finger direction and palm normal from character-space vectors"""
    fw = yawv(yaw); rt = Vector((-fw.y, fw.x, 0)) * -1
    tw = lambda v: (rt * v[0] + fw * v[1] + Vector((0, 0, v[2]))).normalized()
    return tw(fwd), tw(palm)

# ---------------------------------------------------------------- props: key object world transform per frame
def key_obj(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None:
        o.rotation_mode = "XYZ"; o.rotation_euler = rot; o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None: o.scale = scale; o.keyframe_insert("scale", frame=f)

def bone_world(arm, bone):
    return arm.matrix_world @ arm.pose.bones[bone].matrix

def bake_follow(o, arm, bone, f0, f1, offset=Matrix.Identity(4), step=2):
    """bake an object to follow a pose bone (after the rig is keyed). Clears parent."""
    o.parent = None
    for f in list(range(f0, f1 + 1, step)) + [f1]:
        sc.frame_set(f); M = bone_world(arm, bone) @ offset
        o.matrix_world = M
        o.keyframe_insert("location", frame=f); o.rotation_mode = "XYZ"; o.keyframe_insert("rotation_euler", frame=f)

# ---------------------------------------------------------------- camera: Catmull-Rom through (frame, pos, target, lens)
def build_camera(cam, keys, step=1):
    pk = [(k[0], Vector(k[1])) for k in keys]; tk = [(k[0], Vector(k[2])) for k in keys]
    lk = [(k[0], k[3]) for k in keys]; rk = [(k[0], k[4] if len(k) > 4 else 0.0) for k in keys]
    P, T, Ln, Rl = catmull(pk), catmull(tk), catmull(lk), catmull(rk)
    f0, f1 = keys[0][0], keys[-1][0]
    for f in range(f0, f1 + 1, step):
        p = P(f); t = T(f)
        q = (t - p).to_track_quat("-Z", "Y") @ Quaternion((0, 0, 1), R_(Rl(f)))
        cam.location = p; cam.keyframe_insert("location", frame=f)
        cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = q; cam.keyframe_insert("rotation_quaternion", frame=f)
        cam.data.lens = Ln(f); cam.data.keyframe_insert("lens", frame=f)
        cam.data.dof.focus_distance = max(0.05, (t - p).length); cam.data.keyframe_insert("dof.focus_distance", frame=f)
    return P, T

def emit_mat(name, color, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True
    bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Emission Color"].default_value = color + (1,); bs.inputs["Emission Strength"].default_value = strength
    bs.inputs["Base Color"].default_value = color + (1,)
    return m

# ---------------------------------------------------------------- acting helpers (v004 acting pass)
def clear_keys(idb, f0, f1, prefix=None):
    """remove keyframes in [f0, f1] (optionally only on data paths containing prefix)"""
    for fc in fcurves_of(idb):
        if prefix and prefix not in fc.data_path: continue
        for k in [k for k in fc.keyframe_points if f0 <= k.co.x <= f1][::-1]:
            fc.keyframe_points.remove(k)

def _feet_keys(H, f, feet, yaw):
    for s in "LR":
        xy, fy = feet[s][0], feet[s][1]
        H.key_foot(s, f, Vector(xy), fy)

def sit_down(H, f0, f1, sit_root, yaw, feet, z_stand, end_spine=(20, 0, 0), end_head=(15, 0), hands_end=None):
    """stand -> sit with real in-betweens: hips go back and down while the chest leans forward,
    hands slide onto the thighs, feet stay planted."""
    fx = (Vector(feet["L"][0]) + Vector(feet["R"][0])) / 2
    stand = Vector((fx.x, fx.y, z_stand)) + (Vector((sit_root.x, sit_root.y, 0)) - Vector((fx.x, fx.y, 0))) * 0.25
    stand.z = z_stand
    for u, lean, hd in ((0.0, 4, 5), (0.35, 30, 18), (0.7, 34, 20), (1.0, end_spine[0], end_head[0])):
        f = round(f0 + (f1 - f0) * u)
        uu = smooth(min(1.0, u / 0.85))
        r = stand.lerp(Vector(sit_root), uu)
        r.z = z_stand + (sit_root.z - z_stand) * smooth(min(1.0, max(0.0, (u - 0.15) / 0.75)))
        knee = rel(r, yaw, (0, 0.36, 0.13))
        hands = {"L": (knee + rel(Vector(), yaw, (-0.12, 0.0, 0.0)), *hand_dirs(yaw, (0, 1, -0.3), (0, 0, -1)), None),
                 "R": (knee + rel(Vector(), yaw, (0.12, 0.0, 0.0)), *hand_dirs(yaw, (0, 1, -0.3), (0, 0, -1)), None)}
        if u == 1.0 and hands_end: hands = hands_end
        pose(H, f, r, yaw=yaw, flex=-4 * uu, feet=feet, spine=(lean, 0, 0), head=(hd, end_head[1] * u), hands=hands, fingers={"L": "flat_palm", "R": "flat_palm"} if hands else None)

def stand_up(H, f0, f1, sit_root, yaw, feet, z_stand, push=True):
    """sit -> stand: lean forward over the feet, push on the thighs, rise, straighten."""
    fx = (Vector(feet["L"][0]) + Vector(feet["R"][0])) / 2
    top = Vector((fx.x, fx.y, z_stand)) + (Vector((sit_root.x, sit_root.y, 0)) - Vector((fx.x, fx.y, 0))) * 0.15
    top.z = z_stand
    for u, lean, hd in ((0.0, 24, 15), (0.3, 40, 10), (0.45, 32, 6), (0.6, 22, 0), (1.0, 2, 0)):
        f = round(f0 + (f1 - f0) * u)
        r = Vector(sit_root).lerp(top, smooth(min(1.0, u / 0.7)))
        r.z = sit_root.z + (z_stand - sit_root.z) * smooth(min(1.0, max(0.0, (u - 0.2) / 0.8)))
        knee = rel(r, yaw, (0, 0.34, 0.18)) if u < 0.4 else None
        hands = {s: (knee + rel(Vector(), yaw, ((1 if s == "R" else -1) * 0.12, 0, 0)), *hand_dirs(yaw, (0, 1, -0.3), (0, 0, -1)), None) for s in "LR"} if knee is not None else None
        if 0.4 < u < 0.5:
            hands = {s: (rel(r, yaw, ((1 if s == "R" else -1) * 0.34, 0.22, 0.05)), *hand_dirs(yaw, (0, 0.5, -1), ((1 if s == "R" else -1) * -1, 0, 0)), None) for s in "LR"}
        pose(H, f, r, yaw=yaw, feet=feet, spine=(lean, 0, 0), head=(hd, 0), hands=hands, fingers={"L": "flat_palm", "R": "flat_palm"} if hands else None)
    return top

def turn_steps(H, f0, f1, pos, yaw0, yaw1, z):
    """turn on the spot in two real steps (left foot, then right), hips rotating between them"""
    pos = Vector((pos[0], pos[1], z)); fm = round((f0 + f1) / 2)
    for s in "LR":
        H.key_foot(s, f0, H.foot_xy(s, pos, yaw0), yaw0)
    ym = (yaw0 + yaw1) / 2
    # left step
    H.key_foot("L", round(f0 + (fm - f0) * 0.5), H.foot_xy("L", pos, ym).lerp(H.foot_xy("L", pos, yaw0), 0.5), ym, 0.07)
    H.key_foot("L", fm, H.foot_xy("L", pos, yaw1), yaw1); H.key_foot("R", fm, H.foot_xy("R", pos, yaw0), yaw0)
    H.key_foot("R", round(fm + (f1 - fm) * 0.5), H.foot_xy("R", pos, ym).lerp(H.foot_xy("R", pos, yaw1), 0.5), ym + 10, 0.07)
    for s in "LR": H.key_foot(s, f1, H.foot_xy(s, pos, yaw1), yaw1)
    for f in range(f0, f1 + 1, 2):
        u = smooth((f - f0) / max(1, f1 - f0)); y = yaw0 + (yaw1 - yaw0) * u
        H.key_root(f, pos + Vector((0, 0, -0.01 - 0.015 * math.sin(math.pi * u))), yaw=y)
        H.key_spine(f, flex=3, twist=(yaw1 - yaw0) * 0.1 * (1 - u), head=(0, (yaw1 - yaw0) * 0.12 * (1 - u)))
        for s, sg in (("L", -1), ("R", 1)):
            W = rel(pos, y, (sg * 0.36, 0.06, -0.02)); d, n = hand_dirs(y, (0, 0.15, -1), (-sg, 0, 0))
            H.key_hand(s, f, W, d, n, rel(pos, y, (sg * 0.5, -0.45, 0.25)))

# ---------------------------------------------------------------- shared hand-pose library (director, pipeline/hand_poses.py)
exec(open("/home/user/Muhammed/blender/pipeline/hand_poses.py").read())
_POSE_CACHE = {}
def _pose_for(amt):
    return "wrap_grip" if amt >= 0.85 else ("cup_hold" if amt >= 0.6 else ("relaxed" if amt >= 0.25 else "open_alarm"))
def grip(H, s, f, amt=1.0, thumb=0.7, spread=0.0, pose_name=None):
    """finger pose from the shared library (cached per rig/side/pose), keyed at f"""
    pn = pose_name or _pose_for(amt); rig = H.r.o; key = (rig.name, s, pn)
    if key not in _POSE_CACHE:
        sc.frame_set(0); _POSE_CACHE[key] = _pose_rots(rig, s, pn)
    _key(rig, s, _POSE_CACHE[key], f, 1.0)
def mesh_of(name):
    o = bpy.data.objects[name]
    if o.type == "MESH": return o
    ms = [c for c in o.children_recursive if c.type == "MESH"]
    return max(ms, key=lambda c: len(c.data.vertices))
def gripo(H, s, f, obj, point, approach, finger_dir=None):
    """real contact grip on a prop (hand_poses.grip_object); falls back silently if the solver fails"""
    try:
        grip_object(H.r.o, s, int(f), obj, Vector(point), Vector(approach), finger_dir=Vector(finger_dir) if finger_dir is not None else None)
    except Exception as e:
        print("GRIP_FAIL", H.r.o.name, s, f, obj.name, e)
