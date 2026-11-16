"""Aim-based FK posing for MPFB rigs (exec'd). Directions are given in the RIG's rest frame:
+Z up, -Y = the way the character faces, +X = the character's left. key_pose(rig, frame, spec)."""
import bpy, math
from mathutils import Vector, Matrix, Quaternion
R_ = math.radians
def V(*a): return Vector(a).normalized()
def sph(fwd, up, side=0.0):
    """direction from angles (deg): fwd = tilt toward -Y (face side), side = tilt toward +X (char left), from +Z"""
    f, s = R_(fwd), R_(side)
    return Vector((math.sin(s), -math.sin(f), math.cos(f) * math.cos(s))).normalized() * (1 if up else -1)
CHAINS = {  # bone groups that share one aim
    "spine": ["spine05", "spine04", "spine03", "spine02", "spine01"],
    "neck": ["neck01", "neck02", "neck03"], "head": ["head"],
    "uarm.L": ["upperarm01.L", "upperarm02.L"], "farm.L": ["lowerarm01.L", "lowerarm02.L"], "hand.L": ["wrist.L"],
    "uarm.R": ["upperarm01.R", "upperarm02.R"], "farm.R": ["lowerarm01.R", "lowerarm02.R"], "hand.R": ["wrist.R"],
    "thigh.L": ["upperleg01.L", "upperleg02.L"], "shin.L": ["lowerleg01.L", "lowerleg02.L"], "foot.L": ["foot.L"],
    "thigh.R": ["upperleg01.R", "upperleg02.R"], "shin.R": ["lowerleg01.R", "lowerleg02.R"], "foot.R": ["foot.R"],
}
ORDER = ["spine", "neck", "head", "uarm.L", "farm.L", "hand.L", "uarm.R", "farm.R", "hand.R",
         "thigh.L", "shin.L", "foot.L", "thigh.R", "shin.R", "foot.R"]
def _aim(rig, bn, d, blend=1.0):
    pb = rig.pose.bones[bn]; pb.rotation_mode = 'QUATERNION'
    pb.rotation_quaternion = (1, 0, 0, 0); bpy.context.view_layer.update()
    M = pb.matrix.copy(); y = (M.to_3x3() @ Vector((0, 1, 0))).normalized()
    q = y.rotation_difference(d.normalized())
    if blend < 1.0: q = Quaternion().slerp(q, blend)
    R = q.to_matrix() @ M.to_3x3()
    N = R.to_4x4(); N.translation = M.translation
    pb.matrix = N
    q2 = pb.rotation_quaternion.normalized(); pb.rotation_quaternion = q2
    pb.scale = (1, 1, 1)
    if not bn.startswith("IK_") and bn != "root": pb.location = (0, 0, 0)
    bpy.context.view_layer.update()
def _twist(rig, bn, deg):
    pb = rig.pose.bones[bn]
    pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion((0, 1, 0), R_(deg))
    bpy.context.view_layer.update()
def key_pose(rig, frame, spec, root=None):
    """spec: {chain: Vector dir (rig rest frame)} + optional 'twist': {bone: deg}; root: (loc Vector, Quaternion) for 'root' bone"""
    sc = bpy.context.scene; sc.frame_set(int(frame))
    keyed = []
    rb = rig.pose.bones["root"]; rb.rotation_mode = 'QUATERNION'
    if root is not None:
        rb.location = root[0]; rb.rotation_quaternion = root[1]
    bpy.context.view_layer.update()
    rb.keyframe_insert("location", frame=frame, group="root"); rb.keyframe_insert("rotation_quaternion", frame=frame, group="root")
    tw = spec.get("twist", {})
    for ch in ORDER:
        if ch not in spec: continue
        d = spec[ch]
        bones = CHAINS[ch]
        for i, bn in enumerate(bones):
            if bn not in rig.pose.bones: continue
            _aim(rig, bn, d)
            if bn in tw: _twist(rig, bn, tw[bn])
            pb = rig.pose.bones[bn]; pb.keyframe_insert("rotation_quaternion", frame=frame, group=bn); keyed.append(bn)
    for bn, deg in tw.items():
        if bn in keyed: continue
        pb = rig.pose.bones[bn]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion((0, 1, 0), R_(deg))
        pb.keyframe_insert("rotation_quaternion", frame=frame, group=bn)
    return keyed
def key_obj(o, frame, loc=None, rot=None, interp='CONSTANT'):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=frame)
    if rot is not None: o.rotation_euler = rot; o.keyframe_insert("rotation_euler", frame=frame)
def const_interp(o):
    ad = o.animation_data
    if ad and ad.action:
        for fc in _fcurves(ad.action):
            for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
def _fcurves(act):
    if hasattr(act, "fcurves") and len(getattr(act, "fcurves", [])):
        return list(act.fcurves)
    out = []
    for ly in getattr(act, "layers", []):
        for st in ly.strips:
            for cb in st.channelbags: out += list(cb.fcurves)
    return out
