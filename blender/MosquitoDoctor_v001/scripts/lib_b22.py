# B22 helpers (exec'd after anim_lib.py + hand_poses.py). Character staging adapted from B08 BatBite 05_anim.py.
import math, bpy
from mathutils import Vector, Matrix, Quaternion
V = Vector; D = bpy.data.objects; sc = bpy.context.scene
def Rx(d): return Matrix.Rotation(R_(d), 3, 'X')
def Ry(d): return Matrix.Rotation(R_(d), 3, 'Y')
def Rz(d): return Matrix.Rotation(R_(d), 3, 'Z')
RIG, HUM, ARM_L = {}, {}, {}
def setup_human(n):
    RIG[n] = make_human_ctrl(D[n]); HUM[n] = Human(RIG[n]); add_hand_limits(D[n])
    for s in "LR":   # MPFB rest elbow ~46 deg: open the IK limit so arms can straighten (no A-pose)
        lo = D[n].pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = R_(-40); lo.ik_max_x = R_(140)
def rest_head(n, bone): return RIG[n].BN[bone].head_local.copy()
def body_R(yaw=0.0, flex=0.0, side=0.0): return Rz(yaw) @ Rx(flex) @ Ry(side)
def bw(n, P, Rb, local): return P + Rb @ (local - HUM[n].root_head)
def key_foot_free(n, s, f, W, Rw, pole=None):
    H = HUM[n]; a = H.ankle[s]
    M = Matrix.Translation(W) @ Rw.to_4x4() @ Matrix.Translation(-a) @ H.r.rest("IK_foot." + s)
    H.r.key_world("IK_foot." + s, f, M)
    if pole is None: pole = W + Rw @ V((0, -0.7, 0.45))
    pb = H.r.PB["Pole_knee." + s]; nm = "Pole_knee." + s
    pb.location = H.r.rest(nm).to_3x3().inverted() @ (pole - H.r.BN[nm].head_local); pb.keyframe_insert("location", frame=f, group=nm)
def relaxed_hand(n, P, Rb, s, fwd=0.0, out=0.0, up=0.0):
    sx = 1 if s == "L" else -1
    sh = rest_head(n, "upperarm01." + s); wr = rest_head(n, "wrist." + s)
    L = (sh - wr).length
    loc = sh + V((sx * (0.07 + out), -fwd, -L * 0.93 + up))
    W = bw(n, P, Rb, loc)
    d = Rb @ V((0, -0.15 * fwd - 0.05, -1)).normalized(); nn = Rb @ V((-sx, 0, 0))
    return W, d, nn
def elbow_pole(n, P, Rb, s, back=0.55, out=0.25, down=-0.1):
    sx = 1 if s == "L" else -1
    return bw(n, P, Rb, rest_head(n, "lowerarm01." + s) + V((out * sx, back, down)))
def key_hand(n, s, f, W, d, nn, pole=None, P=None, Rb=None):
    if pole is None: pole = elbow_pole(n, P, Rb, s)
    HUM[n].key_hand(s, f, W, d, nn, pole)
def key_relaxed(n, f, P, Rb, sides="LR", pose="relaxed"):
    for s in sides:
        W, d, nn = relaxed_hand(n, P, Rb, s)
        key_hand(n, s, f, W, d, nn, P=P, Rb=Rb); apply_pose(D[n], s, pose, f)
def stand_feet(n, f, x, y, yaw, width=1.0, fwdL=0.0, fwdR=0.0, z=0.0):
    H = HUM[n]; Rw = Rz(yaw)
    for s, fw in (("L", fwdL), ("R", fwdR)):
        a = H.ankle[s]; loc = V((x, y, z)) + Rw @ V((a.x * width, a.y - H.root_head.y - fw, a.z))
        key_foot_free(n, s, f, loc, Rw)
def stand(n, f, x, y, yaw=0.0, flex=0.0, side=0.0, spine=0.0, twist=0.0, head=(0.0, 0.0), dz=0.0, hands=True, feet=True, z=0.0):
    H = HUM[n]
    P = V((x, y, z + H.root_head.z - 0.02 + dz)); Rb = body_R(yaw, flex, side)
    H.key_root(f, P, yaw=yaw, flex=flex, side=side); H.key_spine(f, flex=spine, twist=twist, head=head)
    if feet: stand_feet(n, f, x, y, yaw, z=z)
    if hands: key_relaxed(n, f, P, Rb)
    return P, Rb
def sit(n, f, x, y, seat_z, yaw=0.0, lean=0.0, spine=0.0, twist=0.0, head=(0.0, 0.0), knee_fwd=0.42, width=1.15, breathe=0.0):
    """seated on a chair at (x,y) facing yaw (0 = -y). root over the seat; feet planted forward on the floor (IK bends hip+knee)"""
    H = HUM[n]; Rb = body_R(yaw, lean, 0)
    P = V((x, y, seat_z + 0.10 + breathe * 0.004)); H.key_root(f, P, yaw=yaw, flex=lean)
    H.key_spine(f, flex=spine + breathe * 1.5, twist=twist, head=head)
    Rw = Rz(yaw)
    for s in "LR":
        a = H.ankle[s]; loc = V((x, y, 0)) + Rw @ V((a.x * width, -knee_fwd, a.z))
        key_foot_free(n, s, f, loc, Rw, pole=loc + Rw @ V((0, -0.8, 0.6)))
    return P, Rb
def lie(n, f, head_xy, mattress_z, toward=(0, 1), head=(0.0, 0.0), breathe=0.0, hip_up=0.09):
    """lying on the back, face up, head at head_xy, body extending along `toward` (unit xy). Rb maps rest-up -> toward."""
    H = HUM[n]
    yaw = math.degrees(math.atan2(-toward[0], toward[1])) + 180.0    # rest up(+z) -> +y after Rx(-90); then yaw
    Rb = Rz(yaw) @ Rx(-90)
    top = rest_head(n, "head")
    P0 = V((head_xy[0], head_xy[1], 0)) + Rz(yaw) @ V((0, -(top.z - H.root_head.z), 0))   # hip position along the bed
    P = V((P0.x, P0.y, mattress_z + hip_up + breathe * 0.003))
    H.r.key_world("root", f, Matrix.Translation(P) @ Rb.to_4x4() @ Matrix.Translation(-H.root_head) @ H.r.rest("root"))
    H.key_spine(f, flex=breathe * 1.0, head=head)
    for s in "LR":
        a = H.ankle[s]; W = bw(n, P, Rb, V((a.x * 1.15, a.y, a.z)))
        key_foot_free(n, s, f, W, Rb, pole=W + Rb @ V((0, -0.6, 0.5)))
    return P, Rb
def jaw(n, f, deg): RIG[n].key_rot("jaw", f, [("X", deg)])
def key_ikhand_matrix(n, s, f, M, clamp=True):
    if clamp:
        if (n, s) not in ARM_L: ARM_L[n, s] = (RIG[n].BN["upperarm01." + s].head_local - RIG[n].BN["wrist." + s].head_local).length
        sc.frame_set(int(f)); sh = D[n].pose.bones["upperarm01." + s].head
        v = M.translation - sh
        if v.length > 0.92 * ARM_L[n, s]:
            M = M.copy(); M.translation = sh + v.normalized() * 0.92 * ARM_L[n, s]
    pb = D[n].pose.bones["IK_hand." + s]; Rr = RIG[n].rest("IK_hand." + s)
    loc, q, _ = (Rr.inverted() @ M).decompose()
    if pb.rotation_quaternion.dot(q) < 0: q = -q
    pb.location = loc; pb.rotation_quaternion = q
    pb.keyframe_insert("location", frame=f, group=pb.name); pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
def bone_world(n, bone): return D[n].matrix_world @ D[n].pose.bones[bone].matrix
def key_obj(o, f, M=None, loc=None):
    o.rotation_mode = 'QUATERNION'
    if M is not None: o.matrix_world = M
    if loc is not None: o.location = loc
    o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_quaternion", frame=f)
def key_vis(o, f, show):
    for c in [o] + list(o.children_recursive):
        c.hide_render = not show; c.hide_viewport = not show
        c.keyframe_insert("hide_render", frame=f); c.keyframe_insert("hide_viewport", frame=f)
def skin_tint(n, f, rgb, strength):
    g = [x for x in D[n + ".body"].data.materials[0].node_tree.nodes if x.type == 'GROUP'][0]
    g.inputs['colorMixIn'].default_value = (*rgb, 1); g.inputs['colorMixInStrength'].default_value = strength
    g.inputs['colorMixIn'].keyframe_insert("default_value", frame=f); g.inputs['colorMixInStrength'].keyframe_insert("default_value", frame=f)
def eye_white(n, f, rgb):
    hp = [c for c in D[n].children if "high-poly" in c.name][0]
    g = [x for x in hp.data.materials[0].node_tree.nodes if x.type == 'GROUP'][0]
    g.inputs['EyeWhiteColor'].default_value = (*rgb, 1); g.inputs['EyeWhiteColor'].keyframe_insert("default_value", frame=f)
def ray_down(p, objs, up=0.5):
    """first hit going down from p+up against the evaluated meshes in objs: (point, normal) in world"""
    dg = bpy.context.evaluated_depsgraph_get(); best = None
    for o in objs:
        e = o.evaluated_get(dg); Mi = e.matrix_world.inverted()
        from mathutils.bvhtree import BVHTree
        bvh = BVHTree.FromObject(e, dg)
        o0 = Mi @ (p + V((0, 0, up))); d = (Mi.to_3x3() @ V((0, 0, -1))).normalized()
        h = bvh.ray_cast(o0, d)
        if h[0] is not None:
            w = e.matrix_world @ h[0]
            if best is None or w.z > best[0].z: best = (w, (e.matrix_world.to_3x3().inverted().transposed() @ h[1]).normalized())
    return best
