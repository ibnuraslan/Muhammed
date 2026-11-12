"""CH4/CH5 (chat B): callbacks in the Herrmann hallway, chat A's house set (sc_house), seen from NEW angles.
Night, police gear on the phone table, no people in frame.
  line_end (CH4 chain, last link, label "Court reconstruction"): from halfway up the stairs, looking down
           over the banister at the police reel recorder turning beside the rotary phone
  offhook  (CH5 final): floor level from the far end of the hall, slow push toward the phone table;
           the receiver lies off the hook, the reels slow and stop; silence
"""
import math
import bpy
from mathutils import Vector
from common import ease
import sc_house as H
import b_common as B

EXPOSURE = getattr(H, "EXPOSURE", 0.0)
BOUNCES = getattr(H, "BOUNCES", 6)
DUR = {"line_end": 5.0, "offhook": 7.0}
VARIANT_FOR = {"line_end": "night+police", "offhook": "night+police"}
T = H.PHONE_T


def build(variant=None):
    c = H.build(variant or "night+police")
    # the receiver off the hook for the final shot: lying on the table beside the phone, cord slack
    c["hs_rest"] = (c["handset"].location.copy(), c["handset"].rotation_euler.copy())
    return c


def _spin(c, sec, rate):
    d = c.get("deck")
    if not d:
        return
    d["reels"][0].rotation_euler.z = -rate * 2 * math.pi * 0.75
    d["reels"][1].rotation_euler.z = -rate * 2 * math.pi


def anim(c, t, move):
    sec = t * DUR[move]
    try:
        H._clock(c, sec)
    except Exception:
        pass
    if move == "line_end":
        B.label(c, "Court reconstruction")
        _spin(c, sec, 0.9 * sec)                                     # revolutions so far at ~0.9 rev/s
        if c.get("deck"):
            c["deck"]["needle"].rotation_euler.z = math.radians(-35 + 20 * (0.5 + 0.5 * math.sin(sec * 9.0)) * (0.6 + 0.4 * math.sin(sec * 2.3)))
    else:
        hs = c["handset"]
        hs.matrix_parent_inverse.identity()
        hs.location = Vector((T.x - 0.08, T.y - 0.42, 0.80)); hs.rotation_euler = (math.radians(90), 0, math.radians(15))
        # reels slow to a stop by ~4.5 s: angle = integral of a linearly falling rate
        stop = 4.5; r0 = 0.9
        s_ = min(sec, stop); revs = r0 * s_ - 0.5 * (r0 / stop) * s_ * s_
        _spin(c, sec, revs)
        if c.get("deck"):
            c["deck"]["needle"].rotation_euler.z = math.radians(-35 + 8 * max(0.0, 1 - sec / stop) * math.sin(sec * 9.0))
    bpy.context.view_layer.update()


def cam(a, b, tgt, lens):
    return lambda c, t: (Vector(a).lerp(Vector(b), ease(t)), Vector(tgt), lens)


MOVES = {
    "line_end": dict(kind="anim", dof=None, cam=cam((-0.55, -0.05, 1.72), (-0.42, -0.45, 1.62), (T.x - 0.02, T.y + 0.13, 0.82), 40),
                     anim=lambda c, t: anim(c, t, "line_end"), focus=lambda c, t: Vector((T.x - 0.02, T.y + 0.13, 0.85))),
    "offhook": dict(kind="anim", dof=2.0, cam=cam((-0.9, 2.2, 0.3), (-0.45, -0.2, 0.5), (T.x - 0.05, T.y - 0.2, 0.75), 35),
                    anim=lambda c, t: anim(c, t, "offhook"), focus=lambda c, t: Vector((T.x - 0.08, T.y - 0.42, 0.8))),
}
