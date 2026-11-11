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
        o.hide_render = True; o.keyframe_insert("hide_render", frame=-1)
        for f0, f1 in ranges:
            o.hide_render = False; o.keyframe_insert("hide_render", frame=f0)
            o.hide_render = True; o.keyframe_insert("hide_render", frame=f1 + 1)
        o.hide_render = not any(f0 <= 0 <= f1 for f0, f1 in ranges)
        if o.animation_data and o.animation_data.action:
            for fc in fcurves_of(o):
                for k in fc.keyframe_points: k.interpolation = "CONSTANT"
        o.hide_viewport = False

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
            W = rel(root, yaw + spine[1], ((1 if s == "R" else -1) * 0.24, 0.02, -0.1)); d, n = hand_dirs(yaw, (0, 0.1, -1), ((1 if s == "R" else -1) * -1, 0, 0))
            H.key_hand(s, f, W, d, n, rel(root, yaw, ((1 if s == "R" else -1) * 0.5, -0.45, 0.25)))
            if not (fingers and s in fingers): grip(H, s, f, 0.3, 0.3)
        if fingers and s in fingers:
            grip(H, s, f, fingers[s])

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
