# Shared helpers (from AshaDegree asha_lib, exec after anim_lib.py and hand_poses.py).
import math, bpy
from mathutils import Vector, Matrix

def setup_char(rig):
    """IK feet + IK hands with poles (anim_lib), hand limits, elbow IK limit opened below the MPFB 46 deg rest bend."""
    R = make_human_ctrl(rig)
    add_hand_limits(rig)
    for s in "LR":
        lo = rig.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-40); lo.ik_max_x = math.radians(140)
    H = Human(R); H.rig = rig
    B = R.BN
    H.sh = {s: B["upperarm01." + s].head_local.copy() for s in "LR"}
    H.arm = (B["upperarm01.L"].head_local - B["lowerarm01.L"].head_local).length + (B["lowerarm01.L"].head_local - B["wrist.L"].head_local).length
    return H

def Rz(yaw): return Matrix.Rotation(math.radians(yaw), 3, 'Z')

def to_arm(rig, p):
    """world point -> armature space (rigs may be scaled)"""
    return rig.matrix_world.inverted() @ Vector(p)

def body_hand(H, s, f, pos, yaw, off, d, n, pole_off=None, crouch=0.0):
    """key a wrist target given in the body frame (x right = +X for L, y = -Y forward, z up) relative to the root position"""
    Rm = Rz(yaw)
    W = pos + Rm @ Vector(off)
    if pole_off is None:
        sx = 1 if s == "L" else -1
        pole_off = Vector((0.35 * sx, 0.45, off[2] + 0.25))
    H.key_hand(s, f, W, Rm @ Vector(d), Rm @ Vector(n), pole=pos + Rm @ Vector(pole_off))

def hang_off(H, s, fwd=0.0, swing=0.0, bend=0.03):
    """wrist offset (relative to the root head) for a relaxed hanging arm, slight elbow bend; fwd/swing move it forward (-Y)"""
    sh = H.sh[s] - H.root_head
    sx = 1 if s == "L" else -1
    z = sh.z - H.arm * 0.965 + abs(swing) * 0.2
    return (sh.x + (0.03 + 0.05 * max(0.0, -swing) / 0.08) * sx, sh.y - bend - fwd - swing, z)

def key_hang(H, f, pos, yaw, swingL=0.0, swingR=0.0, fwd=0.0):
    for s, sw in (("L", swingL), ("R", swingR)):
        sx = 1 if s == "L" else -1
        body_hand(H, s, f, pos, yaw, hang_off(H, s, fwd, sw), (0.0, -0.15, -1.0), (-sx, 0.0, 0.0))

def walk_with_arms(H, path, yaw_fn, f0, f1, stride=1.0, amp=0.08, step=2, **kw):
    """anim_lib Human.walk plus opposite arm swing keyed in the body frame"""
    kw.setdefault("crouch", 0.0); kw.setdefault("lean", 3.0); kw.setdefault("bob", 0.015)
    H.walk(path, yaw_fn, f0, f1, stride=stride, step=step, **kw)
    dist = 0.0; prev = path(f0)
    for f in range(f0, f1 + 1):
        p = path(f); dist += (p - prev).to_2d().length; prev = p
        if (f - f0) % step and f != f1: continue
        ph = 2 * math.pi * dist / stride
        # left leg swings forward at phase 0..0.5 -> right arm forward then
        key_hang(H, f, Vector((p.x, p.y, H.root_head.z)), yaw_fn(f), swingL=-amp * math.sin(ph), swingR=amp * math.sin(ph))

def attach(o, rig, bone):
    """Child Of a pose bone keeping the current world placement (no offset drift)"""
    bpy.context.view_layer.update()
    pb = rig.pose.bones[bone]
    c = o.constraints.new('CHILD_OF'); c.target = rig; c.subtarget = bone
    c.inverse_matrix = (rig.matrix_world @ pb.matrix).inverted()
    return c

def dup_char(rig, new):
    """full copy of a character (armature + children + their constraints), meshes shared"""
    nr = rig.copy(); nr.data = rig.data.copy(); nr.name = new; nr.animation_data_clear()
    bpy.context.scene.collection.objects.link(nr)
    for ch in rig.children:
        c = ch.copy(); c.name = new + "." + ch.name.split(".", 1)[1]; c.parent = nr
        c.animation_data_clear()
        for m in c.modifiers:
            if m.type == 'ARMATURE': m.object = nr
        bpy.context.scene.collection.objects.link(c)
    for o in list(bpy.data.objects):
        for con in o.constraints:
            if con.type == 'CHILD_OF' and con.target == rig and o.name.startswith(rig.name + "_"):
                c = o.copy(); c.name = new + o.name[len(rig.name):]; bpy.context.scene.collection.objects.link(c)
                for cc in c.constraints:
                    if cc.type == 'CHILD_OF': cc.target = nr
    return nr

def key_vis(obj_names, frames_on):
    """objects visible only inside the given [f0,f1] ranges (hide_render AND hide_viewport keyed together, constant)"""
    for n in obj_names:
        o = bpy.data.objects[n]
        for f in (0,): o.hide_render = True; o.hide_viewport = True; o.keyframe_insert("hide_render", frame=0); o.keyframe_insert("hide_viewport", frame=0)
        for f0, f1 in frames_on:
            o.hide_render = False; o.hide_viewport = False; o.keyframe_insert("hide_render", frame=f0); o.keyframe_insert("hide_viewport", frame=f0)
            o.hide_render = True; o.hide_viewport = True; o.keyframe_insert("hide_render", frame=f1 + 1); o.keyframe_insert("hide_viewport", frame=f1 + 1)

# ---- from AshaDegree 04_shots
def vis_char(rig, ranges, extra=()):
    names = [c.name for c in rig.children if not c.hide_render]
    props = [o for o in bpy.data.objects if any(c.type == 'CHILD_OF' and c.target == rig for c in o.constraints)]
    for o in props: names += [o.name] + [c.name for c in o.children if not c.hide_render]
    key_vis(names + list(extra), ranges)

def squat(H, f, pos, yaw, depth=0.42, flex=22.0, head=(0.0, 0.0), twist=0.0, feet_wide=1.25, hands=None):
    """deep crouch: feet planted, knees forward (IK), torso leaning; hands rest on the knees unless given"""
    rig = H.rig; Rm = Rz(yaw)
    p = Vector((pos.x, pos.y, H.root_head.z * (1 - depth)))
    p += Rm @ Vector((0, 0.10, 0))   # hips go back
    H.key_root(f, p, yaw=yaw, flex=flex * 0.5)
    H.key_spine(f, flex=flex, twist=twist, head=head)
    for s in "LR":
        sx = 1 if s == "L" else -1
        xy = Vector((pos.x, pos.y)) + (Rm @ Vector((H.ankle[s].x * feet_wide, 0.02, 0))).to_2d()
        H.key_foot(s, f, xy, yaw + sx * 12)
    if hands is None:
        for s in "LR":
            sx = 1 if s == "L" else -1
            kn = Vector((H.ankle[s].x * 1.3, -0.30, H.root_head.z * 0.53 - (H.root_head.z * (1 - depth))))
            body_hand(H, s, f, p, yaw, (kn.x, kn.y, kn.z + 0.05), (0, -1.0, -0.6), (-sx * 0.3, 0, -1.0), pole_off=(0.5 * sx, 0.2, 0.0))
    else:
        hands(p)
    return p

def cam_shot(sid, keys, lens=35, target_keys=None, clip_start=0.05):
    """camera with a smooth path; keys = [(frame, loc)], target_keys = [(frame, point)] (Track To, world up)"""
    c = bpy.data.cameras.new("CAM_" + sid); c.lens = lens; c.clip_start = clip_start; c.clip_end = 600
    c.dof.use_dof = False; c.sensor_width = 36
    o = bpy.data.objects.new("CAM_" + sid, c); sc.collection.objects.link(o)
    t = bpy.data.objects.new("TGT_" + sid, None); sc.collection.objects.link(t)
    for f, p in keys:
        o.location = p; o.keyframe_insert("location", frame=f)
    for f, p in target_keys:
        t.location = p; t.keyframe_insert("location", frame=f)
    for ob in (o, t):
        if ob.animation_data:
            for fc in ob.animation_data.action.fcurves if hasattr(ob.animation_data.action, "fcurves") else []:
                for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'; kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
    tr = o.constraints.new('TRACK_TO'); tr.target = t; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
    m = sc.timeline_markers.new(sid, frame=SH[sid][2]); m.camera = o
    return o

