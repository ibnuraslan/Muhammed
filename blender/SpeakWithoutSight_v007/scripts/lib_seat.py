"""SpeakWithoutSight v007: seating, joint limits and contact helpers (exec'd after anim_lib, hand_poses, lib_anim)."""
import bpy, math
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree

def joint_limits(rig, CT):
    """natural joints: knees and elbows bend one way only, hips stay in a sane cone (IK limits on the solved chains)."""
    upd()
    for s in "LR":
        # --- knee: find the sign that moves the ankle BACKWARD (+Y, the rig faces -Y) = natural flex
        pb = rig.pose.bones["lowerleg01." + s]; q0 = pb.rotation_quaternion.copy()
        a0 = Wh(rig, "foot." + s)
        pb.rotation_quaternion = Quaternion((1, 0, 0), math.radians(30)); upd(); a1 = Wh(rig, "foot." + s)
        pb.rotation_quaternion = q0; upd()
        ksign = 1 if (a1 - a0).y > 0 else -1
        pb.use_ik_limit_x = True; pb.use_ik_limit_y = True; pb.use_ik_limit_z = True
        if ksign > 0: pb.ik_min_x, pb.ik_max_x = math.radians(0), math.radians(150)
        else: pb.ik_min_x, pb.ik_max_x = math.radians(-150), math.radians(0)
        pb.ik_min_y = pb.ik_max_y = 0.0; pb.ik_min_z = pb.ik_max_z = 0.0
        # --- hip: the knee goes forward (-Y) on natural flex; allow 125 deg forward, 15 back, +-30 out/in, +-25 twist
        pb = rig.pose.bones["upperleg01." + s]; q0 = pb.rotation_quaternion.copy()
        k0 = Wh(rig, "lowerleg01." + s)
        pb.rotation_quaternion = Quaternion((1, 0, 0), math.radians(30)); upd(); k1 = Wh(rig, "lowerleg01." + s)
        pb.rotation_quaternion = q0; upd()
        hsign = 1 if (k1 - k0).y < 0 else -1
        pb.use_ik_limit_x = pb.use_ik_limit_y = pb.use_ik_limit_z = True
        if hsign > 0: pb.ik_min_x, pb.ik_max_x = math.radians(-15), math.radians(125)
        else: pb.ik_min_x, pb.ik_max_x = math.radians(-125), math.radians(15)
        pb.ik_min_y, pb.ik_max_y = math.radians(-25), math.radians(25)
        pb.ik_min_z, pb.ik_max_z = math.radians(-30), math.radians(30)
        # --- elbow: flex only (MPFB rest elbow is bent: allow it to open 40 deg to straight, never past)
        pb = rig.pose.bones["lowerarm01." + s]
        esign = 1          # MPFB default rig: the elbow flexes on +X (hand_poses / BellyFat v018 assume the same)
        pb.use_ik_limit_x = True; pb.use_ik_limit_y = True; pb.use_ik_limit_z = True
        if esign > 0: pb.ik_min_x, pb.ik_max_x = math.radians(-35), math.radians(140)
        else: pb.ik_min_x, pb.ik_max_x = math.radians(-140), math.radians(35)
        pb.ik_min_y = pb.ik_max_y = 0.0; pb.ik_min_z = pb.ik_max_z = 0.0
        # --- shoulder cone (upperarm01): no wild twist
        pb = rig.pose.bones["upperarm01." + s]; pb.use_ik_limit_y = True; pb.ik_min_y, pb.ik_max_y = math.radians(-60), math.radians(60)
    return {"knee": ksign, "hip": hsign, "elbow": esign}

def bvh_eval(obj):
    upd(); dg = bpy.context.evaluated_depsgraph_get(); e = obj.evaluated_get(dg); me = e.to_mesh(); Mw = obj.matrix_world
    b = BVHTree.FromPolygons([Mw @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons]); e.to_mesh_clear(); return b

def ray_surface(objs, origin, direction, dist=5.0):
    best = None
    for o in objs:
        h = bvh_eval(o).ray_cast(Vector(origin), Vector(direction).normalized(), dist)
        if h[0] is not None and (best is None or h[3] < best[3]): best = h
    return best

def eval_body_points(obj, bones_prefix, rig):
    """world positions of evaluated body verts whose dominant deform bone starts with one of bones_prefix"""
    db = DOMB.get(obj.name)
    if db is None:
        db = dom_bones(obj, rig); DOMB[obj.name] = db
    saved = []
    for m in obj.modifiers:
        if m.type in ('MASK', 'SUBSURF'): saved.append((m, m.show_viewport)); m.show_viewport = False
    upd(); dg = bpy.context.evaluated_depsgraph_get(); e = obj.evaluated_get(dg); me = e.to_mesh()
    out = [obj.matrix_world @ v.co for v in me.vertices if db.get(v.index) and db[v.index].startswith(bones_prefix)]
    e.to_mesh_clear()
    for m, sv in saved: m.show_viewport = sv
    upd(); return out
DOMB = {}
