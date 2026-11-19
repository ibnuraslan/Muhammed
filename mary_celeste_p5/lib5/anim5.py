"""Part 5 animation layer (final render). Same moves as Part 1 (mary_celeste_p1/p1/anim.py), written for Part 5's
scenes. Nothing moves by itself:

  camera_move(cam, move, dur, handheld)   eased, motivated camera moves: push / pull / drift / rise / tilt / spin / hold
  ocean_time(dur)                         the FFT sea advances with the shot clock (every Ocean modifier)
  ride(rec, dur)                          a boat rides the real wave surface frame by frame (float_on re-solved on the
                                          animated sea); whoever and whatever is in it goes with it
  sail(root, dur, speed, heave, roll)     the ship goes on her way before the wind (S04-S06: she moves away)
  sway(root, dur, ...)                    a ship at anchor / alongside a quay: the swell works her a little
  steam(dur), flicker(dur)                steam rising off the mugs; lamp and lantern flames breathing
"""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix, Quaternion

FPS = 24


def _interp(kind):
    try:
        bpy.context.preferences.edit.keyframe_new_interpolation_type = kind
    except Exception:
        pass


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def aim(cam, loc, tgt, roll=0.0):
    cam.location = loc
    q = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y')
    if roll:
        q = q @ Quaternion((0, 0, 1), math.radians(roll))
    cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = q


def camera_move(cam, move, dur, handheld=0.0, seed=3):
    loc0 = cam.location.copy(); q0 = cam.rotation_quaternion.copy()
    fwd = q0 @ Vector((0, 0, -1)); right = q0 @ Vector((1, 0, 0)); up = q0 @ Vector((0, 1, 0))
    dist = cam.data.dof.focus_distance if cam.data.dof.use_dof else 6.0
    tgt0 = loc0 + fwd * dist
    rng = np.random.default_rng(seed); ph = rng.uniform(0, 6.28, 4)
    n = int(round(dur * FPS)) + 1
    _interp('BEZIER')
    for i in range(n):
        t = i / FPS; u = ease(t / max(dur, 1e-3))
        kind = move[0]; loc = loc0.copy(); tgt = tgt0.copy(); roll = 0.0
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
            tgt = loc0 + Quaternion(right, math.radians(move[1] * u)) @ (tgt0 - loc0)
        elif kind == "spin":                         # top-down: turn slowly about the view axis
            roll = move[1] * u
        if handheld:
            sway = right * math.sin(0.7 * 6.28 * t + ph[0]) + up * math.sin(0.53 * 6.28 * t + ph[1])
            tgt = tgt + sway * handheld * (tgt - loc).length * 0.004
            roll += handheld * 0.25 * math.sin(0.37 * 6.28 * t + ph[3])
        aim(cam, loc, tgt, roll)
        if cam.data.dof.use_dof:
            cam.data.dof.focus_distance = max(0.2, dist - (loc - loc0).dot(fwd))
            cam.data.dof.keyframe_insert("focus_distance", frame=1 + i)
        cam.keyframe_insert("location", frame=1 + i); cam.keyframe_insert("rotation_quaternion", frame=1 + i)


def ocean_time(dur, speed=1.0):
    _interp('LINEAR')
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        for md in o.modifiers:
            if md.type == 'OCEAN':
                t0 = md.time
                md.keyframe_insert("time", frame=1)
                md.time = t0 + dur * speed; md.keyframe_insert("time", frame=1 + int(round(dur * FPS)))
                md.time = t0
    _interp('BEZIER')


def adopt(root, half=(3.3, 1.2), z=(-1.5, 3.0), names=("painter",)):
    """Parent to the boat root every free object that sits inside it (crew, clothes, hair, props) or is named for it."""
    bpy.context.view_layer.update()
    Mi = root.matrix_world.inverted(); n = 0
    for o in list(bpy.data.objects):
        if o.parent is not None or o is root or o.type in ('LIGHT', 'CAMERA') or o.name.startswith(("Ocean", "FarSea", "Sun")):
            continue
        q = Mi @ o.matrix_world.to_translation()
        named = any(k in o.name for k in names)
        if named or (abs(q.x) < half[0] and abs(q.y) < half[1] and z[0] < q.z < z[1]):
            mw = o.matrix_world.copy(); o.parent = root; o.matrix_world = mw; n += 1
    return n


def ride(rec, dur, step=2):
    """rec = (ocean, root, heading, x, y, kwargs) as given to boatsea.float_on in the scene. Re-solve the float on the
    animated sea every `step` frames and key the boat there (the sea cut inside the hull follows the root)."""
    import boatsea
    oc, root, hd, x, y, kw = rec
    gns = [m for m in oc.modifiers if m.type == 'NODES']
    sc = bpy.context.scene
    keys = []
    import time
    t0 = time.time()
    for i in range(0, int(round(dur * FPS)) + step, step):
        sc.frame_set(1 + i)
        if i == step:
            print(f"RIDE {root.name}: {time.time() - t0:.1f}s per sample", flush=True)
        for m in gns:
            m.show_viewport = False                  # sample the sea itself, not the sea with the hull cut out of it
        getattr(boatsea, "float_on_raw", boatsea.float_on)(oc, root, hd, x, y, **kw)
        for m in gns:
            m.show_viewport = True
        keys.append((1 + i, root.matrix_world.copy()))
    _interp('BEZIER')
    root.rotation_mode = 'QUATERNION'
    for f, M in keys:
        loc, q, s = M.decompose()
        root.location = loc; root.rotation_quaternion = q
        root.keyframe_insert("location", frame=f); root.keyframe_insert("rotation_quaternion", frame=f)
    sc.frame_set(1)


def _children_follow(root):
    return [o for o in bpy.data.objects if o.parent is root]


def sail(root, dur, speed=2.6, heave=0.25, roll=1.5, pitch=0.6, period=7.0, seed=5):
    """The ship goes on her way: forward along her heading at `speed` m/s, the swell lifting and rolling her."""
    base = root.matrix_world.copy()
    fwd = base.to_3x3() @ Vector((1, 0, 0)); fwd.z = 0; fwd.normalize()
    rng = np.random.default_rng(seed); p = rng.uniform(0, 6.28, 3); w = 2 * math.pi / period
    root.rotation_mode = 'XYZ'
    _interp('BEZIER')
    for i in range(0, int(round(dur * FPS)) + 3, 2):
        t = i / FPS
        R = Matrix.Translation(fwd * speed * t + Vector((0, 0, heave * math.sin(w * t + p[0])))) @ base @ \
            Matrix.Rotation(math.radians(roll * math.sin(w * 0.83 * t + p[1])), 4, 'X') @ \
            Matrix.Rotation(math.radians(pitch * math.sin(w * 1.21 * t + p[2])), 4, 'Y')
        root.matrix_world = R
        root.keyframe_insert("location", frame=1 + i); root.keyframe_insert("rotation_euler", frame=1 + i)
    root.matrix_world = base


def sway(root, dur, heave=0.08, roll=0.8, pitch=0.3, period=8.0, seed=2):
    sail(root, dur, speed=0.0, heave=heave, roll=roll, pitch=pitch, period=period, seed=seed)


def steam(dur, rise=0.35):
    """Steam off the mugs: the wisp pattern rises through the volume (its noise lookup slides down over time)."""
    for m in bpy.data.materials:
        if not m.use_nodes or not any(n.type == 'VOLUME_PRINCIPLED' for n in m.node_tree.nodes):
            continue
        N = m.node_tree.nodes; L = m.node_tree.links
        nz = next((n for n in N if n.type == 'TEX_NOISE'), None)
        if nz is None or not nz.inputs['Vector'].links:
            continue
        src = nz.inputs['Vector'].links[0].from_socket
        mp = N.new("ShaderNodeMapping"); L.new(src, mp.inputs['Vector']); L.new(mp.outputs[0], nz.inputs['Vector'])
        _interp('LINEAR')
        mp.inputs['Location'].default_value = (0, 0, 0); mp.inputs['Location'].keyframe_insert("default_value", frame=1)
        mp.inputs['Location'].default_value = (0.05, 0, -rise * dur); mp.inputs['Location'].keyframe_insert("default_value", frame=1 + int(round(dur * FPS)))
        _interp('BEZIER')


def flicker(dur, amount=0.12, seed=7):
    """Flames breathe: every warm point light (lamp, lantern) varies a little in strength, keyed every 2 frames."""
    rng = np.random.default_rng(seed)
    for o in bpy.data.objects:
        if o.type != 'LIGHT' or o.data.type != 'POINT':
            continue
        c = o.data.color
        if not (c[0] > c[2] * 1.2):
            continue
        e0 = o.data.energy; ph = rng.uniform(0, 6.28, 3)
        for i in range(0, int(round(dur * FPS)) + 3, 2):
            t = i / FPS
            k = 1 + amount * (0.6 * math.sin(2 * math.pi * 1.3 * t + ph[0]) + 0.3 * math.sin(2 * math.pi * 3.7 * t + ph[1])
                              + 0.1 * math.sin(2 * math.pi * 7.1 * t + ph[2]))
            o.data.energy = e0 * k; o.data.keyframe_insert("energy", frame=1 + i)
        o.data.energy = e0
