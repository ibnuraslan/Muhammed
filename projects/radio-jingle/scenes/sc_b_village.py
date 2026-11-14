"""Chat B storyboard v2, 3-3B: "Werner Mazurek lives a few hundred meters from the Herrmanns."
Chat A's village (sc_village, read-only), afternoon low sun. From above the family's garden gate, a red survey cord
runs itself along the lane, past the gardens, to the gate of a house further down; the camera rises and travels
with it until both houses are in one frame. A real object on the road, not a graphic. No people.
"""
import math
import bpy
from mathutils import Vector
from kit import *
from common import ease
import b_common as B
import b_fx as F

EXPOSURE = 0.0
DUR = {"distance": 7.0}
VARIANT_FOR = {"distance": "afternoon"}
A_GATE = Vector((-2.4, -3.4, 0.03))
B_GATE = Vector((56.0, 3.4, 0.03))           # the gate of a house further down the lane (unnamed, north side)


def build(variant=None):
    import sc_village as V
    c = V.build("afternoon")
    pts = [A_GATE, Vector((-2.4, -1.6, 0.03))]
    for k in range(1, 12):
        x = -2.4 + (B_GATE.x - (-2.4)) * k / 12
        pts.append(Vector((x, -1.6 + 0.05 * math.sin(k * 1.3), 0.03)))
    pts += [Vector((B_GATE.x, 1.6, 0.03)), B_GATE]
    c["cord"] = F.curve("SurveyCord", pts, pbr("CordRed", (0.62, 0.06, 0.04), 0.6), bevel=0.035, smooth=True)
    F.draw(c["cord"], 0.0)
    # stakes at both gates, where the cord is tied
    for nm, p in (("StakeA", A_GATE), ("StakeB", B_GATE)):
        cyl(nm, p + Vector((0, 0, 0.3)), 0.03, 0.6, pbr("StakeWood", (0.45, 0.32, 0.18), 0.8), verts=10)
        box(nm + "Cap", p + Vector((0, 0, 0.62)), (0.08, 0.08, 0.04), pbr("StakeRed", (0.65, 0.07, 0.04), 0.5))
    B.preview_cap()
    return c


def anim(c, t, move):
    F.draw(c["cord"], ease(min(1.0, max(0.0, (t - 0.12) / 0.66))))
    bpy.context.view_layer.update()


def cam_dist(c, t):
    """Start above the family's gate, travel east with the cord's head while rising; end with both gates in frame."""
    e = ease(t)
    head_x = -2.4 + (B_GATE.x + 2.4) * ease(min(1.0, max(0.0, (t - 0.12) / 0.66)))
    tgt = Vector((head_x * 0.55 + 27.0 * 0.45 * e, -1.0, 0.0)).lerp(Vector((27.0, 0.0, 0.0)), e)
    pos = Vector((-12.0 + 30.0 * e, -26.0 - 14.0 * e, 14.0 + 22.0 * e))
    return pos, tgt, 32


MOVES = {"distance": dict(kind="anim", dof=None, cam=cam_dist, anim=lambda c, t: anim(c, t, "distance"))}
