"""Shared animation helpers, copied from BellyFat_v018 (rebuild10). Needs anim_lib.py + hand_poses.py exec'd first."""
import bpy, bmesh, math
from mathutils import Vector, Matrix, Quaternion, Euler
from mathutils.bvhtree import BVHTree
sc = bpy.context.scene
O = bpy.data.objects

def upd(): bpy.context.view_layer.update()
def fs(f): sc.frame_set(int(f))
def W(rig, bone): return rig.matrix_world @ rig.pose.bones[bone].matrix
def Wh(rig, bone): return rig.matrix_world @ rig.pose.bones[bone].head
def Wt(rig, bone): return rig.matrix_world @ rig.pose.bones[bone].tail

def iter_fcurves(action):
    try:
        for fc in action.fcurves: yield fc
    except AttributeError:
        for layer in action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for fc in cb.fcurves: yield fc

def set_interp(obj_or_data, kind='CONSTANT', path_contains=None):
    ad = obj_or_data.animation_data
    if not ad or not ad.action: return
    for fc in iter_fcurves(ad.action):
        if path_contains and path_contains not in fc.data_path: continue
        for kp in fc.keyframe_points: kp.interpolation = kind

def frame_from(y_dir, z_hint, origin):
    y = Vector(y_dir).normalized(); z = Vector(z_hint); z = (z - y * z.dot(y)).normalized(); x = y.cross(z)
    M = Matrix((x, y, z)).transposed().to_4x4(); M.translation = Vector(origin); return M

def dom_bones(body, rig):
    names = {b.name for b in rig.data.bones}; i2n = {g.index: g.name for g in body.vertex_groups if g.name in names}
    out = {}
    for v in body.data.vertices:
        best = (0, None)
        for g in v.groups:
            n = i2n.get(g.group)
            if n and g.weight > best[0]: best = (g.weight, n)
        out[v.index] = best[1]
    return out

def eval_points(obj, filt=None):
    saved = []
    for m in obj.modifiers:
        if m.type in ('MASK', 'SUBSURF'): saved.append((m, m.show_viewport)); m.show_viewport = False
    upd(); dg = bpy.context.evaluated_depsgraph_get(); e = obj.evaluated_get(dg); me = e.to_mesh()
    pts = [(v.index, obj.matrix_world @ v.co, (obj.matrix_world.to_3x3() @ v.normal).normalized()) for v in me.vertices
           if filt is None or filt(v.index)]
    e.to_mesh_clear()
    for m, sv in saved: m.show_viewport = sv
    upd()
    return pts

def world_bvh(obj):
    upd(); dg = bpy.context.evaluated_depsgraph_get(); e = obj.evaluated_get(dg); me = e.to_mesh()
    Mw = obj.matrix_world
    b = BVHTree.FromPolygons([Mw @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons]); e.to_mesh_clear(); return b

def ray_down(objs, x, y, z0=3.0):
    best = None
    for o in objs:
        b = world_bvh(o); hit = b.ray_cast(Vector((x, y, z0)), Vector((0, 0, -1)), 10.0)
        if hit[0] is not None and (best is None or hit[0].z > best): best = hit[0].z
    return best

def smoothstep(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

# ------------------------------------------------------------------ FK helpers (from EarInArm v015)
def aim_bone(rig, name, direction, f=1):
    upd(); pb = rig.pose.bones[name]; cur = pb.matrix.copy()
    y = cur.col[1].to_3d().normalized(); q = y.rotation_difference(Vector(direction).normalized())
    R = q.to_matrix() @ cur.to_3x3().normalized()
    M = R.to_4x4(); M.translation = cur.translation; pb.matrix = M; upd()
    pb.keyframe_insert("rotation_quaternion", frame=f, group=name)

# ------------------------------------------------------------------ props owned by hands / heads (Child Of switching, R4)
def key_basis(obj, f, M):
    loc, q, s = M.decompose(); obj.rotation_mode = 'QUATERNION'
    if obj.rotation_quaternion.dot(q) < 0: q = -q
    obj.location = loc; obj.rotation_quaternion = q; obj.scale = s
    for k in ("location", "rotation_quaternion", "scale"): obj.keyframe_insert(k, frame=f)
    ad = obj.animation_data
    if ad and ad.action:
        for fc in iter_fcurves(ad.action):
            for kp in fc.keyframe_points:
                if abs(kp.co.x - f) < 0.5 and not fc.data_path.startswith("constraints"): kp.interpolation = 'LINEAR'


def bone_world(target, sub):
    return target.matrix_world @ target.pose.bones[sub].matrix if sub else target.matrix_world.copy()

OWN = {}
def owner_switch(obj, f, target=None, sub=None, log=print):
    """from frame f the prop is owned by `target`(.sub) via Child Of, or by nobody (static); world kept continuous"""
    fs(f - 1); Wprev = obj.matrix_world.copy()
    obj.rotation_mode = 'QUATERNION'
    for k_ in ("location", "rotation_quaternion", "scale"): obj.keyframe_insert(k_, frame=f - 1)
    for c in obj.constraints:
        if c.type != 'CHILD_OF': continue
        c.keyframe_insert("influence", frame=f - 1); c.influence = 0.0; c.keyframe_insert("influence", frame=f)
    if target is None:
        key_basis(obj, f, Wprev)
        set_interp(obj, 'LINEAR')
    else:
        c = obj.constraints.new('CHILD_OF'); c.name = "own_%d" % f; c.target = target
        if sub: c.subtarget = sub
        c.influence = 0.0; c.keyframe_insert("influence", frame=0); c.keyframe_insert("influence", frame=f - 1)
        c.influence = 1.0; c.keyframe_insert("influence", frame=f)
        fs(f)
        c.inverse_matrix = bone_world(target, sub).inverted() @ Wprev
        key_basis(obj, f, Matrix.Identity(4))
    set_interp(obj, 'LINEAR')
    fs(f); log("owner", obj.name, f, target.name if target else None, sub, "jump_mm", round((obj.matrix_world.translation - Wprev.translation).length * 1000, 2))
    OWN.setdefault(obj.name, []).append((f, target.name if target else None, sub))

def active_child(obj):
    for c in obj.constraints:
        if c.type == 'CHILD_OF' and c.influence > 0.5: return c
    return None

def key_world_while_owned(obj, f, Mworld):
    """key the basis so the prop sits at world matrix Mworld at frame f under its active owner"""
    fs(f); c = active_child(obj)
    if c is None: key_basis(obj, f, Mworld); return
    P = bone_world(c.target, c.subtarget) @ c.inverse_matrix
    key_basis(obj, f, P.inverted() @ Mworld)

def vis(obj, f, show):
    obj.hide_render = not show; obj.hide_viewport = not show
    obj.keyframe_insert("hide_render", frame=f); obj.keyframe_insert("hide_viewport", frame=f)
    set_interp(obj, 'CONSTANT', "hide")

def quat_continuity(obj):
    if not obj.animation_data or not obj.animation_data.action: return 0
    groups = {}
    for fc in iter_fcurves(obj.animation_data.action):
        if fc.data_path.endswith("rotation_quaternion"): groups.setdefault(fc.data_path, {})[fc.array_index] = fc
    nfix = 0
    for dp, ch in groups.items():
        if len(ch) != 4: continue
        frames = sorted({kp.co.x for kp in ch[0].keyframe_points})
        idx = [{round(kp.co.x, 3): kp for kp in ch[i].keyframe_points} for i in range(4)]
        prev = None
        for fr in frames:
            kps = [idx[i].get(round(fr, 3)) for i in range(4)]
            if any(k is None for k in kps): continue
            q = Quaternion([k.co.y for k in kps])
            if prev is not None and prev.dot(q) < 0:
                for k in kps:
                    k.co.y = -k.co.y; k.handle_left.y = -k.handle_left.y; k.handle_right.y = -k.handle_right.y
                q = -q; nfix += 1
            prev = q
        for c in ch.values(): c.update()
    return nfix

# ================================================================== face rig helpers (directions solved numerically per rig)
_NUDGE = {}
def nudge_q(rig, bone, want, deg):
    key = (rig.name, bone, tuple(round(x, 2) for x in want))
    if key not in _NUDGE:
        pb = rig.pose.bones[bone]; q0 = pb.rotation_quaternion.copy(); upd()
        base = Wt(rig, bone); best = None
        for ax in ((1, 0, 0), (0, 0, 1), (0, 1, 0)):
            for sg in (1, -1):
                pb.rotation_quaternion = Quaternion(ax, math.radians(10 * sg)); upd()
                d = (Wt(rig, bone) - base).dot(Vector(want).normalized())
                if best is None or d > best[0]: best = (d, ax, sg)
        pb.rotation_quaternion = q0; upd()
        _NUDGE[key] = best
    d, ax, sg = _NUDGE[key]
    return Quaternion(ax, math.radians(deg * sg))

def face_dirs(rig):
    """world directions of the face at rest-orientation of the root (rig faces -Y at rest)"""
    return Vector((0, -1, 0)), Vector((0, 0, 1))

def key_face(rig, f, smile=0.0, jaw=0.0, brow=0.0, squint=0.0, pucker=0.0):
    """expressions as bone nudges (rest-relative). smile 0..1, jaw 0..1 open, brow -1(frown)..1(raised), squint 0..1"""
    up = Vector((0, 0, 1))
    for s, sx in (("L", 1), ("R", -1)):
        out = Vector((sx, 0, 0))
        for b, amt in (("risorius03." + s, 14), ("levator05." + s, 10), ("oris04." + s, 8)):
            if b in rig.pose.bones:
                q = nudge_q(rig, b, up + out * 0.7, amt) if smile >= 0 else nudge_q(rig, b, -up + out * 0.2, amt)
                pb = rig.pose.bones[b]; pb.rotation_quaternion = Quaternion().slerp(q, abs(smile)); pb.keyframe_insert("rotation_quaternion", frame=f)
        for b in ("oculi01." + s, "oculi02." + s):
            if b in rig.pose.bones:
                q = nudge_q(rig, b, up, 10) if brow >= 0 else nudge_q(rig, b, -up - out * 0.5, 10)
                pb = rig.pose.bones[b]; pb.rotation_quaternion = Quaternion().slerp(q, abs(brow)); pb.keyframe_insert("rotation_quaternion", frame=f)
        b = "orbicularis04." + s     # lower lid up for squint
        if b in rig.pose.bones:
            q = nudge_q(rig, b, up, 12); pb = rig.pose.bones[b]; pb.rotation_quaternion = Quaternion().slerp(q, squint); pb.keyframe_insert("rotation_quaternion", frame=f)
    q = nudge_q(rig, "jaw", -up, 14); pb = rig.pose.bones["jaw"]; pb.rotation_quaternion = Quaternion().slerp(q, jaw); pb.keyframe_insert("rotation_quaternion", frame=f)

def blinks(rig, frames, close_deg=26):
    for s in "LR":
        b = "orbicularis03." + s; pb = rig.pose.bones[b]
        q = nudge_q(rig, b, Vector((0, 0, -1)), close_deg)
        pb.rotation_quaternion = Quaternion(); pb.keyframe_insert("rotation_quaternion", frame=1)
        for bf in frames:
            for df, u in ((0, 0), (3, 1), (6, 1), (11, 0)):
                pb.rotation_quaternion = Quaternion().slerp(q, u); pb.keyframe_insert("rotation_quaternion", frame=bf + df)

def eyes_closed(rig, f0, f1, ramp=8):
    for s in "LR":
        b = "orbicularis03." + s; pb = rig.pose.bones[b]; q = nudge_q(rig, b, Vector((0, 0, -1)), 26)
        for f, u in ((f0, 0), (f0 + ramp, 1), (f1 - ramp, 1), (f1, 0)):
            pb.rotation_quaternion = Quaternion().slerp(q, u); pb.keyframe_insert("rotation_quaternion", frame=f)

def saccades(ctrl, f0, f1, every=40, amp=(3, 5), seed=1):
    rnd = random.Random(seed)
    for f in range(f0, f1, every):
        for s in "LR":
            ctrl.key_rot("eye." + s, f, [("X", rnd.uniform(-amp[0], amp[0])), ("Z", rnd.uniform(-amp[1], amp[1]))])

def breathe(ctrl, f0, f1, base_flex, per=200, amp=1.2, twist=0.0):
    for f in range(f0, f1 + 1, 20):
        key_spine(ctrl, f, flex=base_flex(f) + amp * math.sin(2 * math.pi * f / per), twist=twist)

