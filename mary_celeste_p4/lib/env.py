"""Shim for lib/anim.py (from Part 1): FPS and aim()."""
import math
from mathutils import Vector, Quaternion
FPS = 24


def aim(obj, loc, target, roll=0.0):
    obj.location = Vector(loc)
    q = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y')
    if roll:
        q = q @ Quaternion((0, 0, 1), math.radians(roll))
    obj.rotation_mode = 'QUATERNION'; obj.rotation_quaternion = q
