"""Look-dev of the typewriter alone."""
import math
import bpy
from mathutils import Vector
from kit import *
import typewriter as T
EXPOSURE = 0.0
def build(variant=None):
    c = {}
    world_flat((0.05, 0.055, 0.06), 1.0)
    box("Desk", (0, 0, -0.01), (1.4, 1.0, 0.02), pbr("Desk", (0.3, 0.27, 0.24), 0.5))
    k = area_light((-0.5, -0.6, 0.8), (0, 0, 0), 0.6, 40, (1, 0.95, 0.9)); point_at(k, (0, 0, 0.1))
    f = area_light((0.6, -0.2, 0.5), (0, 0, 0), 0.8, 12, (0.8, 0.9, 1)); point_at(f, (0, 0, 0.1))
    r = area_light((0.0, 0.6, 0.6), (0, 0, 0), 0.8, 20, (0.9, 0.95, 1)); point_at(r, (0, 0, 0.1))
    c["tw"] = T.make("TW", text="Moscow, May 1984.\nThe quick brown fox jumps.", bugged=True)
    return c
def anim(c, t):
    T.type_at(c["tw"], t * 6.0)
MOVES = {
    "three": dict(kind="anim", anim=anim, cam=lambda c, t: (Vector((-0.45, -0.55, 0.42)), Vector((0, 0.0, 0.09)), 50)),
    "ball": dict(kind="anim", anim=anim, cam=lambda c, t: (T.world(c["tw"], (c["tw"]["carrier"].location.x - 0.05, -0.16, 0.2)), T.world(c["tw"], (c["tw"]["carrier"].location.x, 0.01, 0.125)), 70)),
    "inside": dict(kind="anim", anim=lambda c, t: (anim(c, t), T.set_cover(c["tw"], hide=True)), cam=lambda c, t: (Vector((-0.3, -0.4, 0.3)), Vector((0, -0.05, 0.04)), 50)),
}
