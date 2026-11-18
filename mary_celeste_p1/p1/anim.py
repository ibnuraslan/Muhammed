"""Animation layer for the final render (step 2). The storyboard bakes one pose per person; here the rig stays live:

  Actor(kind, M, pose_fn, look_fn)   pose_fn(dv, M, t) poses the rig at time t (seconds into the shot); it is
                                     evaluated at key times and keyframed on every pose bone (Bezier), so the
                                     clothes (skinned shells) follow; strand hair and beard are grown once on the
                                     first pose and ride on the head bone; eyes ride on the head and are aimed
                                     per key; blinks every 3-5 s are added automatically.
  cam_path(keys)                     camera keys [(t, loc, target, lens)], eased between keys, with an optional
                                     slow handheld sway (0.2-0.4 deg, < 1 Hz) for interiors.
  ship_motion(root, ...)             heave / roll / pitch on a ship root (the sea moves her; she never moves by herself).
  ocean_time(ocean, t0, speed)       the FFT sea advances with the shot clock.
Nothing is animated without a cause in the script or the physics (wind, sea, a person's action)."""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix, Quaternion
import env as E
import crew as Cw
import human as H

FPS = E.FPS


def frame(t):
    return 1 + int(round(t * FPS))


class Actor:
    def __init__(self, kind, M, pose_fn, look_fn=None, dur=4.0, key_every=0.25, density=1.0, blink=True, seed=0):
        if kind == "deveau":
            self.dv = Cw.deveau()
        elif kind == "morehouse":
            self.dv = Cw.morehouse()
        else:
            self.dv = Cw.sailor(int(kind))
        self.M = M; self.pose_fn = pose_fn; self.look_fn = look_fn; self.dur = dur
        h = self.dv.h
        rng = np.random.default_rng(seed)
        self.blinks = []
        if blink:
            tb = rng.uniform(0.6, 2.0)
            while tb < dur:
                self.blinks.append(tb); tb += rng.uniform(3.0, 5.0)
        times = sorted(set([round(k * key_every, 4) for k in range(int(dur / key_every) + 1)] + [dur] +
                           [b + d for b in self.blinks for d in (-0.06, 0.0, 0.08, 0.16)]))
        pb = h.arm.pose.bones
        for b in pb:
            b.rotation_mode = 'QUATERNION'
        for t in times:
            if t < 0 or t > dur:
                continue
            H.reset_pose(h)
            pose_fn(self.dv, M, t)
            self._blink(t)
            bpy.context.view_layer.update()
            f = 1 + t * FPS
            for b in pb:
                b.keyframe_insert("rotation_quaternion", frame=f)
                b.keyframe_insert("location", frame=f)
        # first pose: grow hair, ride it on the head bone; aim and park the eyes
        bpy.context.scene.frame_set(1)
        bpy.context.view_layer.update()
        self._grow_hair(density)
        h.arm.matrix_world = M
        bpy.context.view_layer.update()

    def _blink(self, t):
        for b in self.blinks:
            if b - 0.06 < t < b + 0.16:
                self.dv.lids(1.6 * (1 - abs(t - (b + 0.04)) / 0.12) if abs(t - (b + 0.04)) < 0.12 else 0)

    def _grow_hair(self, density):
        dv = self.dv; h = dv.h
        head_M = (h.arm.matrix_world @ h.arm.pose.bones["head"].matrix).copy()
        dv.head_R = head_M.to_3x3() @ h.arm.data.bones["head"].matrix_local.to_3x3().inverted()
        # posed surface without the subsurf (same vertex count as the rest mesh) for the hair roots
        sub = [m for m in h.body.modifiers if m.type == 'SUBSURF']
        for m in sub:
            m.show_viewport = False
        dg = bpy.context.evaluated_depsgraph_get()
        oe = h.body.evaluated_get(dg); me = oe.to_mesh()
        P = np.array([v.co[:] for v in me.vertices]); oe.to_mesh_clear()
        from mathutils.bvhtree import BVHTree
        bvh = BVHTree.FromObject(h.body, dg)
        for m in sub:
            m.show_viewport = True
        dv._posed_surface = lambda: (P, bvh)
        dv._grow_all(density)
        for o in [o for o in dv.hair_objs if o]:
            mw = o.matrix_world.copy(); o.parent = h.arm; o.parent_type = 'BONE'; o.parent_bone = "head"
            bpy.context.view_layer.update(); o.matrix_world = mw
        dv.h.arm.hide_render = True


def cam_path(cam, keys, handheld=0.0, seed=3):
    """keys: [(t, loc, target, lens)]. Keyframes every frame between keys with smoothstep easing (no linear moves)."""
    keys = sorted(keys, key=lambda k: k[0])
    t_end = keys[-1][0]; rng = np.random.default_rng(seed)
    ph = rng.uniform(0, 6.28, 4)
    n = int(round(t_end * FPS)) + 1
    for i in range(n):
        t = i / FPS
        k = max(j for j in range(len(keys)) if keys[j][0] <= t + 1e-6)
        a = keys[k]; b = keys[min(k + 1, len(keys) - 1)]
        u = 0.0 if b[0] == a[0] else (t - a[0]) / (b[0] - a[0]); u = u * u * (3 - 2 * u)
        loc = Vector(a[1]).lerp(Vector(b[1]), u); tgt = Vector(a[2]).lerp(Vector(b[2]), u)
        lens = a[3] + (b[3] - a[3]) * u
        roll = 0.0
        if handheld:
            sway = Vector((math.sin(0.7 * 6.28 * t + ph[0]), math.sin(0.53 * 6.28 * t + ph[1]), math.sin(0.41 * 6.28 * t + ph[2])))
            tgt = tgt + sway * handheld * (tgt - loc).length * 0.006
            roll = handheld * 0.3 * math.sin(0.37 * 6.28 * t + ph[3])
        E.aim(cam, loc, tgt, roll)
        cam.data.lens = lens
        f = 1 + i
        cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_quaternion", frame=f)
        cam.data.keyframe_insert("lens", frame=f)


def ship_motion(root, base, dur, heave=0.25, roll=2.5, pitch=0.8, period=7.5, seed=0):
    """The sea works the ship: slow heave, roll and pitch around her rest placement (keyed every 2 frames)."""
    rng = np.random.default_rng(seed); p = rng.uniform(0, 6.28, 3)
    for i in range(0, int(dur * FPS) + 2, 2):
        t = i / FPS; w = 2 * math.pi / period
        R = Matrix.Translation((0, 0, heave * math.sin(w * t + p[0]))) @ \
            Matrix.Rotation(math.radians(roll * math.sin(w * 0.83 * t + p[1])), 4, 'X') @ \
            Matrix.Rotation(math.radians(pitch * math.sin(w * 1.21 * t + p[2])), 4, 'Y')
        root.matrix_world = base @ R
        root.keyframe_insert("location", frame=1 + i); root.keyframe_insert("rotation_euler", frame=1 + i)


def ocean_time(ocean, t0, dur, speed=1.0):
    md = ocean.modifiers["Ocean"]
    md.time = t0; md.keyframe_insert("time", frame=1)
    md.time = t0 + dur * speed; md.keyframe_insert("time", frame=1 + int(dur * FPS))
    for fc in ocean.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
