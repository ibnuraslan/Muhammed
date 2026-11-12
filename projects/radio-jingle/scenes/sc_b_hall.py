"""CH4/CH5 (chat B): callbacks in the Herrmann hallway, chat A's house set (sc_house), seen from NEW angles.
Night, police gear on the phone table, no people in frame.
  line_end (CH4 chain, last link, label "Court reconstruction"): from halfway up the stairs, looking down
           over the banister at the police reel recorder turning beside the rotary phone
  offhook  (CH5 final): a slow side push onto the phone table at table height;
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
DUR = {"line_end": 5.0, "offhook": 8.0}   # offhook: reels stop at 5.0 s on "answered", then 3 s hold
VARIANT_FOR = {"line_end": "night+police", "offhook": "night+police"}
T = H.PHONE_T


def build(variant=None):
    c = H.build(variant or "night+police")
    # the receiver off the hook for the final shot: lying on the table beside the phone, cord slack
    c["hs_rest"] = (c["handset"].location.copy(), c["handset"].rotation_euler.copy())
    # cap the practicals (the shade clipped to white on sheet 1)
    for k in ("shade_mat", "pshade_mat"):
        if c.get(k):
            bs = c[k].node_tree.nodes["Principled BSDF"]
            bs.inputs['Emission Strength'].default_value = 0.3
            bs.inputs['Transmission Weight'].default_value = 0.0         # the bulb behind the shade blew it out to white
            bs.inputs['Base Color'].default_value = (0.5, 0.38, 0.24, 1)
    for nm in ("HallLampL", "PianoLampL"):
        o = bpy.data.objects.get(nm)
        if o:
            o.data.energy *= 0.35
    B.finish_interior(lift=0.1, faces=0)
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
        if hs.parent is not None:                                    # unparent: it lies on the table, off the hook
            ph_loc = hs.parent.matrix_world.translation.copy()
            hs.parent = None; c["ph_loc"] = ph_loc
        ph_loc = c["ph_loc"]
        hs.rotation_mode = 'XYZ'
        hs.location = Vector((ph_loc.x - 0.24, ph_loc.y - 0.06, 0.815)); hs.rotation_euler = (math.radians(90), 0, math.radians(-70))
        # reels slow to a stop by ~4.5 s: angle = integral of a linearly falling rate
        stop = 5.0; r0 = 0.9
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
    "offhook": dict(kind="anim", dof=2.4, cam=cam((T.x - 1.3, T.y - 0.7, 1.42), (T.x - 0.95, T.y - 0.55, 1.3), (T.x - 0.1, T.y - 0.1, 0.8), 32),
                    anim=lambda c, t: anim(c, t, "offhook"), focus=lambda c, t: Vector((T.x - 0.06, T.y - 0.25, 0.82))),
}
