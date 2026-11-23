"""Shared helpers for the v012 rebuild scripts."""
import math
import bpy
from mathutils import Vector, Matrix, Quaternion
sc = bpy.context.scene
V = lambda *a: Vector(a)

def fcurves(idb):
    ad = getattr(idb, "animation_data", None)
    if not ad or not ad.action: return []
    return [fc for L in ad.action.layers for st in L.strips for cb in st.channelbags for fc in cb.fcurves]

def clear_keys(idb, paths, a=-10**6, b=10**6):
    """remove keys of fcurves whose data_path starts with one of paths, inside [a, b]"""
    for fc in fcurves(idb):
        if any(fc.data_path.startswith(p) for p in paths):
            k = fc.keyframe_points
            for i in reversed(range(len(k))):
                if a <= k[i].co.x <= b: k.remove(k[i], fast=True)
            fc.update()

def key_hide(ob, spans):
    """visible only inside spans [(a,b),...]; constant keys"""
    clear_keys(ob, ("hide_render", "hide_viewport"))
    pts = {0: True}
    for a, b in spans: pts[a] = False; pts[b + 1] = True
    for f in sorted(pts):
        ob.hide_render = pts[f]; ob.keyframe_insert("hide_render", frame=f)
    for fc in fcurves(ob):
        if fc.data_path == "hide_render":
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'

def constant(idb, paths=None):
    for fc in fcurves(idb):
        if paths is None or any(fc.data_path.startswith(p) for p in paths):
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'

def seg_dist(p, a_, b_):
    ab = b_ - a_; t = max(0.0, min(1.0, (p - a_).dot(ab) / max(ab.length_squared, 1e-9))); return (p - (a_ + ab * t)).length

def tool_length(pen):
    zs = []
    for c in [pen] + list(pen.children_recursive):
        if c.type == 'MESH':
            M = pen.matrix_world.inverted() @ c.matrix_world
            zs += [(M @ Vector(v)).z for v in c.bound_box]
    return max(zs) if zs else 0.15

def ik_clear(r, s, a0, b0):
    clear_keys(r, ('pose.bones["IK_hand.%s"]' % s,), a0, b0)

def grip_frame(r, s, frame, up=0.045):
    """pen-in-wrist-space matrix from the evaluated pinch pose at `frame` (pen +Z = tip -> back end, origin at tip)"""
    PB = r.pose.bones
    sc.frame_set(frame)
    Wi = PB["wrist." + s].matrix.inverted()
    loc = lambda b, tail=False: Wi @ (PB[b].tail if tail else PB[b].head)
    c = (loc("finger1-3." + s, True) + loc("finger2-3." + s, True)) / 2
    web = (loc("finger2-1." + s) + loc("finger1-2." + s)) / 2
    u = (web - c).normalized()
    pn = (loc("finger3-1." + s) - loc("wrist." + s)).cross(loc("finger2-1." + s) - loc("finger5-1." + s)).normalized()
    if s == "R": pn = -pn
    X = pn.cross(u).normalized(); Y = u.cross(X)
    T = Matrix((X, Y, u)).transposed().to_4x4(); T.translation = c - u * up
    return T, u

def hold_path(rig_name, s, pen, f0, f1, tip_fn, grip_ref, head_clear=0.20, away=V(1, 0, 0), up=0.045, toward_shoulder=True, use_forearm=True):
    """IK hand keyed every frame so the tool tip follows tip_fn(f) (world), orientation = the rig's own feasible wrist
    orientation swung away from the head; tool then baked from the EVALUATED wrist every frame."""
    r = bpy.data.objects[rig_name]; PB = r.pose.bones; BN = r.data.bones
    Lp = tool_length(pen)
    Rorig = {}
    for f in range(f0, f1 + 1):
        sc.frame_set(f); Rorig[f] = (r.matrix_world.to_3x3() @ PB["wrist." + s].matrix.to_3x3()).normalized()
    T, u = grip_frame(r, s, grip_ref, up)
    Rrel = (PB["lowerarm02." + s].matrix.to_3x3().normalized().inverted() @ PB["wrist." + s].matrix.to_3x3().normalized()) if use_forearm else None
    tipL = T.translation
    W0, I0 = BN["wrist." + s].matrix_local, BN["IK_hand." + s].matrix_local
    ik_clear(r, s, f0, f1)
    pb = PB["IK_hand." + s]
    def put(f, Rw, P0l):
        Hw = Rw.to_4x4(); Hw.translation = P0l - Rw @ tipL
        M_ = (Hw @ W0.inverted()) @ I0; M_.translation = Hw.translation
        pb.matrix = M_; bpy.context.view_layer.update()
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        hd = r.matrix_world @ (PB["head"].head + (PB["head"].tail - PB["head"].head) * 0.5)
        sh = r.matrix_world @ PB["upperarm01." + s].head
        P0 = tip_fn(f); P0l = r.matrix_world.inverted() @ P0
        Ro = Rorig[f]; Uo = (Ro @ u).normalized()
        U = ((sh - P0).normalized() + V(0, 0, 0.6)).normalized() if toward_shoulder else Uo.copy()
        for _ in range(16):
            if seg_dist(hd, P0, P0 + U * Lp) >= head_clear: break
            U = (U + away * 0.12 + V(0, 0, 0.04)).normalized()
        Rq = Uo.rotation_difference(U).to_matrix() @ Ro
        Rw = r.matrix_world.to_3x3().inverted() @ Rq
        cands = [Rw, PB["wrist." + s].matrix.to_3x3().normalized()]
        best = None
        for it in range(9):                       # wrist limits clamp: keep the candidate whose evaluated tip lands
            Rc = cands[it] if it < len(cands) else Rnext
            put(f, Rc, P0l)
            err = ((r.matrix_world @ (PB["wrist." + s].matrix @ T)).translation - P0).length
            if best is None or err < best[0]: best = (err, Rc.copy())
            if err < 0.003: break
            Rnext = PB["wrist." + s].matrix.to_3x3().normalized() if it % 2 == 0 else \
                ((PB["lowerarm02." + s].matrix.to_3x3().normalized() @ Rrel).normalized() if Rrel is not None else PB["wrist." + s].matrix.to_3x3().normalized())
        Rw = best[1]
        put(f, Rw, P0l)
        pb.keyframe_insert("location", frame=f, group=pb.name); pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
    # bake tool
    if pen.animation_data: pen.animation_data_clear()
    pen.rotation_mode = 'QUATERNION'; gap = 0.0
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        M = r.matrix_world @ PB["wrist." + s].matrix @ T
        pen.matrix_world = M
        pen.keyframe_insert("location", frame=f); pen.keyframe_insert("rotation_quaternion", frame=f)
        gap = max(gap, (M.translation - tip_fn(f)).length)
    return gap
