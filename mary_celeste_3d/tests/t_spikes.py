"""Spike QA: strongly bent poses (deep crouch, arms folded hard, head turned) for every shared character;
fails if any evaluated mesh vertex lies more than 0.6 m outside the body's own bounds."""
import sys, os, math; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenes"))
import common as C
C.reset()
import bpy, numpy as np
from mathutils import Vector, Matrix
import human as H, poses as P, deveau as D, women as W, briggs as BR

def bend_hard(c):
    h = c.h
    for sd, sg in H.SIDE.items():
        h.rot(f"upperleg01.{sd}", (1, 0, 0), -95); h.rot(f"lowerleg01.{sd}", (1, 0, 0), 120); h.rot(f"foot.{sd}", (1, 0, 0), -30)
        P.hand_reach(h, sd, h.bone_head("spine03") + Vector((-sg * 0.12, -0.12, 0.05)), elbow=(sg * 1, 0.2, -0.3))
        P.grip(h, sd, 1.0)
    for b in ("spine04", "spine03", "spine02"):
        h.rot(b, (1, 0, 0), 18); h.rot(b, (0, 0, 1), 12)
    P.head(h, pitch=35, yaw=50, tilt=15)

bad = 0
for k, mk in enumerate((lambda: D.Deveau(), lambda: BR.Briggs(), lambda: W.Sarah(seated=True), lambda: W.Sophia(seated=True), lambda: W.Arthur())):
    c = mk(); bend_hard(c); c.finish(density=0.05, place=Matrix.Translation((k * 3.0, 0, 0)))
    dg = bpy.context.evaluated_depsgraph_get()
    be = c.h.body.evaluated_get(dg); bm = be.to_mesh(); B = np.array([be.matrix_world @ v.co for v in bm.vertices]); be.to_mesh_clear()
    lo, hi = B.min(0) - 0.6, B.max(0) + 0.6
    for o in c.objects:
        if o.type != 'MESH':
            continue
        oe = o.evaluated_get(dg); me = oe.to_mesh()
        V = np.array([oe.matrix_world @ v.co for v in me.vertices]) if len(me.vertices) else np.zeros((0, 3)); oe.to_mesh_clear()
        out = ((V < lo) | (V > hi)).any(1).sum() if len(V) else 0
        if out:
            bad += 1; print("SPIKE", c.name, o.name, int(out), "max dist", float(np.abs(V - (lo + hi) / 2).max()))
print("SPIKECHECK", "FAIL" if bad else "OK", bad)
