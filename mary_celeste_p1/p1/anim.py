"""Animation layer for the final render (step 2). The storyboard bakes one pose per person; here the rig stays live:

  live(dv, M, pose, look_w, dur)   pose(dv, M) is the shot's pose; at key times it is re-applied, an idle layer is added
                                   (breathing, a slow weight shift, small head moves), an optional action(dv, M, t)
                                   on top, blinks every 3-5 s; every pose bone is keyed. The clothes (skinned shells)
                                   and buttons follow the rig; strand hair and beard are grown once on the first pose
                                   and ride on the head bone; the eyes ride on the head and are aimed at look_w.
  camera_move(cam, kind, dur)      eased, motivated camera moves: push / pull / drift / rise / tilt / hold(+sway)
  ship_motion(root, dur)           heave / roll / pitch: the sea works the ship (she never moves by herself)
  ocean_time(dur)                  the FFT sea advances with the shot clock (all Ocean modifiers)
Nothing moves without a cause: breath and weight in people, the sea under ships, wind in loose canvas."""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix, Quaternion
import env as E
import human as H
import poses as P

FPS = E.FPS


def _linear_keys():
    try:
        bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
    except Exception:
        pass


def _bezier_keys():
    try:
        bpy.context.preferences.edit.keyframe_new_interpolation_type = 'BEZIER'
    except Exception:
        pass


def idle(dv, t, seed=0):
    """Breathing (0.25 Hz chest), slow weight shift (0.08 Hz hips), small head drift: a standing/seated person alive."""
    h = dv.h; rng = np.random.default_rng(seed); p = rng.uniform(0, 6.28, 4)
    br = math.sin(2 * math.pi * 0.25 * t + p[0])
    h.rot("spine03", (1, 0, 0), -0.9 * br)
    h.rot("spine05", (0, 1, 0), 0.8 * math.sin(2 * math.pi * 0.08 * t + p[1]))
    h.rot("neck02", (0, 0, 1), 1.6 * math.sin(2 * math.pi * 0.11 * t + p[2]))
    h.rot("head", (1, 0, 0), 0.9 * math.sin(2 * math.pi * 0.17 * t + p[3]))


def live(dv, M, pose, look_w, dur, density=1.0, seed=0, action=None, key_every=0.25):
    h = dv.h
    rng = np.random.default_rng(seed + 11)
    blinks = []; tb = rng.uniform(0.5, 1.8)
    while tb < dur:
        blinks.append(tb); tb += rng.uniform(3.0, 5.0)
    times = sorted(set([round(k * key_every, 4) for k in range(int(dur / key_every) + 1)] + [round(dur, 4)] +
                       [round(b + d, 4) for b in blinks for d in (-0.07, 0.0, 0.06, 0.14)]))
    pb = h.arm.pose.bones
    for b in pb:
        b.rotation_mode = 'QUATERNION'
    _bezier_keys()
    for t in times:
        if t < 0 or t > dur + 1e-6:
            continue
        H.reset_pose(h)
        idle(dv, t, seed)          # breathing first: the shot's pose (with its hand IK) goes on top, so hands stay on
        pose(dv, M)                # their rails, spokes and tables while the chest moves
        if action:
            action(dv, M, t)
        for b in blinks:
            u = (t - b) / 0.07
            if -1.0 < u < 2.0:
                dv.lids(1.5 * max(0.0, 1 - abs(u - 0.5) / 1.5))
        bpy.context.view_layer.update()
        f = 1 + t * FPS
        for b in pb:
            b.keyframe_insert("rotation_quaternion", frame=f)
            b.keyframe_insert("location", frame=f)
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    # eyes: aim at the look target from the first pose (in the rig's frame), then they ride the head bone
    if look_w is not None:
        tgt = M.inverted() @ Vector(look_w)
        for e in h.eyes:
            mw = e.matrix_world.copy(); loc = mw.to_translation()
            d = (tgt - loc).normalized()
            R = (-d).to_track_quat('Y', 'Z').to_matrix().to_4x4()
            e.matrix_world = Matrix.Translation(loc) @ R
    bpy.context.view_layer.update()
    _grow_hair(dv, density)
    h.arm.matrix_world = M
    h.arm.hide_render = True
    bpy.context.view_layer.update()


def _grow_hair(dv, density):
    h = dv.h
    head_M = (h.arm.matrix_world @ h.arm.pose.bones["head"].matrix).copy()
    dv.head_R = head_M.to_3x3() @ h.arm.data.bones["head"].matrix_local.to_3x3().inverted()
    sub = [m for m in h.body.modifiers if m.type == 'SUBSURF']
    for m in sub:
        m.show_viewport = False
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    oe = h.body.evaluated_get(dg); me = oe.to_mesh()
    Pts = np.array([v.co[:] for v in me.vertices]); oe.to_mesh_clear()
    from mathutils.bvhtree import BVHTree
    bvh = BVHTree.FromObject(h.body, dg)
    for m in sub:
        m.show_viewport = True
    dv._posed_surface = lambda: (Pts, bvh)
    dv._grow_all(density)
    for o in [o for o in getattr(dv, "hair_objs", []) if o]:
        mw = o.matrix_world.copy(); o.parent = h.arm; o.parent_type = 'BONE'; o.parent_bone = "head"
        bpy.context.view_layer.update(); o.matrix_world = mw


# ----------------------------------------------------------------------------- camera
def camera_move(cam, move, dur, handheld=0.0, seed=3):
    """move: ("push", frac) moves frac of the camera-target distance toward the target over the shot;
    ("pull", frac); ("drift", (dx, dy, dz)) a lateral slide in metres (camera space: right, up, forward);
    ("rise", m); ("tilt", deg) pans the aim up; ("hold",) locked off. Always eased in/out."""
    loc0 = cam.location.copy(); q0 = cam.rotation_quaternion.copy()
    fwd = q0 @ Vector((0, 0, -1)); right = q0 @ Vector((1, 0, 0)); up = q0 @ Vector((0, 1, 0))
    dist = cam.data.dof.focus_distance if cam.data.dof.use_dof else 6.0
    tgt0 = loc0 + fwd * dist
    rng = np.random.default_rng(seed); ph = rng.uniform(0, 6.28, 4)
    n = int(round(dur * FPS)) + 1
    _bezier_keys()
    for i in range(n):
        t = i / FPS; u = t / max(dur, 1e-3); u = u * u * (3 - 2 * u)
        kind = move[0]; loc = loc0.copy(); tgt = tgt0.copy()
        if kind == "push":
            loc = loc0 + (tgt0 - loc0) * move[1] * u
        elif kind == "pull":
            loc = loc0 - (tgt0 - loc0) * move[1] * u
        elif kind == "drift":
            d = move[1]; off = right * d[0] + up * d[1] + fwd * d[2]
            loc = loc0 + off * u; tgt = tgt0 + off * u * 0.6
        elif kind == "rise":
            loc = loc0 + Vector((0, 0, move[1] * u)); tgt = tgt0 + Vector((0, 0, move[1] * u * 0.5))
        elif kind == "tilt":
            ang = math.radians(move[1] * u)
            tgt = loc0 + Quaternion(right, ang) @ (tgt0 - loc0)
        roll = 0.0
        if handheld:
            sway = right * math.sin(0.7 * 6.28 * t + ph[0]) + up * math.sin(0.53 * 6.28 * t + ph[1])
            tgt = tgt + sway * handheld * (tgt - loc).length * 0.004
            roll = handheld * 0.25 * math.sin(0.37 * 6.28 * t + ph[3])
        E.aim(cam, loc, tgt, roll)
        if cam.data.dof.use_dof:
            cam.data.dof.focus_distance = max(0.2, dist - (loc - loc0).dot(fwd))
            cam.data.dof.keyframe_insert("focus_distance", frame=1 + i)
        cam.keyframe_insert("location", frame=1 + i); cam.keyframe_insert("rotation_quaternion", frame=1 + i)


def ship_motion(root, dur, heave=0.18, roll=1.6, pitch=0.6, period=7.0, seed=0):
    """The sea works the ship about her rest placement: slow heave, roll and pitch (keys every 2 frames)."""
    base = root.matrix_world.copy()
    rng = np.random.default_rng(seed); p = rng.uniform(0, 6.28, 3); w = 2 * math.pi / period
    root.rotation_mode = 'XYZ'
    _bezier_keys()
    for i in range(0, int(dur * FPS) + 3, 2):
        t = i / FPS
        R = Matrix.Translation((0, 0, heave * math.sin(w * t + p[0]))) @ \
            Matrix.Rotation(math.radians(roll * math.sin(w * 0.83 * t + p[1])), 4, 'X') @ \
            Matrix.Rotation(math.radians(pitch * math.sin(w * 1.21 * t + p[2])), 4, 'Y')
        root.matrix_world = base @ R
        root.keyframe_insert("location", frame=1 + i); root.keyframe_insert("rotation_euler", frame=1 + i)
    root.matrix_world = base


def ocean_time(dur, speed=1.0):
    _linear_keys()
    for o in bpy.data.objects:
        md = o.modifiers.get("Ocean") if o.type == 'MESH' else None
        if md is None:
            continue
        t0 = md.time
        md.keyframe_insert("time", frame=1)
        md.time = t0 + dur * speed; md.keyframe_insert("time", frame=1 + int(round(dur * FPS)))
        md.time = t0
    _bezier_keys()
