"""Turntable checks for the period vehicles (not used in the film)."""
import math
import bpy
from mathutils import Vector
from kit import box, pbr
import rj, rj_vehicles, vehicles

EXPOSURE = 0.0


def build(variant=None):
    rj.sky("grey")
    box("Ground", (0, 0, -0.01), (80, 80, 0.02), rj.mat("asphalt"))
    c = {}
    c["fiat"] = vehicles.make("fiat600", loc=(0, 0, 0), heading_deg=30, color=(0.78, 0.6, 0.08))
    c["pol"] = vehicles.make("polizei_1981", loc=(5.5, 2.5, 0), heading_deg=-20, lamps=True)
    c["heli"] = vehicles.make("helicopter_police", loc=(-3, 9, 0), heading_deg=60)
    c["boat"] = vehicles.make("boat_police", loc=(7, 10, 0), heading_deg=120)
    return c


MOVES = {"fiat": dict(kind="anim", cam=lambda c, t: (Vector((4.5, -5.5, 1.6)), Vector((0.3, 0, 0.6)), 35)),
         "all": dict(kind="anim", cam=lambda c, t: (Vector((2, -14, 6)), Vector((2, 4, 0.8)), 28))}
